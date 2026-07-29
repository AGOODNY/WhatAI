import json
import random
import re
import secrets

from django.core import signing

from apps.dialogue.services.llm_client import LLMClient
from apps.dialogue.services.private_prompt_builder import build_private_prompt
from apps.users.services.model_selection import get_user_llm_model

from .idiom_data import IDIOMS, OPENING_IDIOMS


GAME_TOKEN_SALT = "what-ai.idiom-game.v1"
MAX_CHAIN_LENGTH = 80
TURN_SECONDS = 60
RULE_SUMMARY = (
    "后一成语首字的读音必须与前一成语末字完全同音同调；字可以不同。"
    "例如“力”lì 可以接“丽”lì，但不能接“离”lí。成语不能重复。"
)


def normalize_idiom(value):
    return "".join(str(value or "").strip().split())


def same_syllable_and_tone(left, right):
    return bool(left and right and left == right)


def _candidates(syllable, used):
    return [
        item for item in IDIOMS.values()
        if item["first"] == syllable and item["word"] not in used
    ]


def _catalog_from_payload(payload):
    catalog = dict(IDIOMS)
    extras = payload.get("extras", {})
    if not isinstance(extras, dict) or len(extras) > MAX_CHAIN_LENGTH:
        raise ValueError("对局凭证无效")

    for word, syllables in extras.items():
        if (
            not isinstance(word, str)
            or len(word) != 4
            or not isinstance(syllables, list)
            or len(syllables) != 2
            or not all(_valid_numbered_pinyin(item) for item in syllables)
        ):
            raise ValueError("对局凭证无效")
        catalog[word] = {
            "word": word,
            "first": syllables[0],
            "last": syllables[1],
        }
    return catalog


def validate_chain(raw_chain, opening, catalog=None):
    catalog = catalog or IDIOMS
    if not isinstance(raw_chain, list) or not 1 <= len(raw_chain) <= MAX_CHAIN_LENGTH:
        raise ValueError("对局记录无效")

    chain = []
    used = set()
    previous = None
    for index, raw_item in enumerate(raw_chain):
        if not isinstance(raw_item, dict):
            raise ValueError("对局记录无效")
        word = normalize_idiom(raw_item.get("word"))
        player = raw_item.get("player")
        expected_player = "ai" if index % 2 == 0 else "user"
        if player != expected_player or word not in catalog or word in used:
            raise ValueError("对局记录无效")
        if index == 0 and word != opening:
            raise ValueError("对局开场不一致")
        if previous and not same_syllable_and_tone(
            catalog[previous]["last"],
            catalog[word]["first"],
        ):
            raise ValueError("对局接龙关系无效")
        chain.append({"word": word, "player": player})
        used.add(word)
        previous = word
    return chain


def validate_submission(word, chain, catalog=None):
    catalog = catalog or IDIOMS
    word = normalize_idiom(word)
    if not re.fullmatch(r"[\u3400-\u9fff]{4}", word):
        return False, "请输入一个四字成语。"
    if word not in catalog:
        return False, "这个成语需要进一步校验。"
    if any(item["word"] == word for item in chain):
        return False, "这个成语已经用过了，不能重复。"

    previous = chain[-1]["word"]
    expected = catalog[previous]["last"]
    actual = catalog[word]["first"]
    if not same_syllable_and_tone(expected, actual):
        return False, (
            f"“{word[0]}”和“{previous[-1]}”不是同音同调，"
            "这次接不上。"
        )
    return True, ""


def _valid_numbered_pinyin(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-zv]+[1-5]", value))


def _normalize_numbered_pinyin(value):
    value = (
        str(value or "")
        .strip()
        .lower()
        .replace("u:", "v")
        .replace("ü", "v")
    )
    return value if _valid_numbered_pinyin(value) else ""


def _extract_json_object(text):
    text = str(text or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def judge_unknown_idiom(*, word, chain, catalog, user):
    """Ask the LLM only when the deterministic dictionary has no entry."""
    previous = chain[-1]["word"]
    expected = catalog[previous]["last"]
    prompt = f"""
你是一个严格的现代汉语成语词典校验器，不进行聊天。

上一成语：{previous}
上一成语末字：{previous[-1]}
接龙要求的首字读音（数字标调拼音）：{expected}
用户提交：{word}

请判断“{word}”是否为规范、固定、通行的四字汉语成语，并给出该成语语境中首字和末字的实际读音。
不要把普通四字短语、人名、地名、网络梗、临时拼接词或仅仅语法通顺的表达当成成语。
多音字必须按这个成语里的真实读音标注。

只输出一个 JSON 对象：
{{"valid": true, "first": "小写拼音+声调数字", "last": "小写拼音+声调数字", "reason": ""}}
或
{{"valid": false, "first": "", "last": "", "reason": "简短中文原因"}}

拼音示例：力和丽都是 li4，离是 li2；ü 使用 v，例如 lv4。不要输出 Markdown 或其他内容。
""".strip()
    reply = LLMClient().generate(
        prompt,
        max_tokens=120,
        temperature=0.0,
        model=get_user_llm_model(user),
    )
    decision = _extract_json_object(reply)
    if not decision:
        return None, "暂时无法确认这个成语，换一个常见成语或稍后重试。"
    if decision.get("valid") is not True:
        reason = str(decision.get("reason") or "").strip()[:80]
        return None, reason or "没有查到它是规范的四字成语。"

    first = _normalize_numbered_pinyin(decision.get("first"))
    last = _normalize_numbered_pinyin(decision.get("last"))
    if not first or not last:
        return None, "暂时无法确认这个成语的准确读音，换一个试试。"
    if not same_syllable_and_tone(expected, first):
        return None, (
            f"“{word[0]}”和“{previous[-1]}”不是同音同调，"
            "这次接不上。"
        )
    return {"word": word, "first": first, "last": last}, ""


def _private_history(persona, history):
    persona_token = str(persona.id)
    result = []
    for item in history[-24:] if isinstance(history, list) else []:
        if not isinstance(item, dict):
            continue
        role = "USER" if item.get("role") == "user" else persona_token
        result.append({
            "role": role,
            "content": str(item.get("content", ""))[:500],
        })
    return result


def _decode_game_token(token, user, persona):
    try:
        payload = signing.loads(
            str(token or ""),
            salt=GAME_TOKEN_SALT,
            max_age=24 * 60 * 60,
        )
    except signing.BadSignature as exc:
        raise ValueError("对局凭证已失效，请重新开局") from exc

    if (
        payload.get("user_id") != user.id
        or payload.get("persona_id") != persona.id
        or payload.get("opening") not in IDIOMS
    ):
        raise ValueError("对局凭证无效")
    _catalog_from_payload(payload)
    return payload


def _encode_game_token(payload):
    return signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)


def create_game_token(user, persona, opening):
    # About 25% of matches give the player a reachable AI stumble after
    # 5-7 genuinely correct answers. The rest keep the AI competitive.
    rng = random.SystemRandom()
    stumble_after = (
        rng.choice((5, 6, 7))
        if rng.random() < 0.25
        else None
    )
    return signing.dumps(
        {
            "user_id": user.id,
            "persona_id": persona.id,
            "opening": opening,
            "stumble_after": stumble_after,
            "nonce": secrets.token_urlsafe(8),
            "extras": {},
        },
        salt=GAME_TOKEN_SALT,
        compress=True,
    )


def choose_opening():
    return random.SystemRandom().choice(OPENING_IDIOMS)


def choose_ai_idiom(chain, catalog=None, competitive=False):
    catalog = catalog or IDIOMS
    used = {item["word"] for item in chain}
    required = catalog[chain[-1]["word"]]["last"]
    options = _candidates(required, used)
    if not options:
        return None

    scored = []
    for option in options:
        followups = len(_candidates(option["last"], used | {option["word"]}))
        scored.append((followups, option))

    user_rounds = sum(item["player"] == "user" for item in chain)
    viable = [pair for pair in scored if pair[0] > 0]
    if viable and (not competitive or user_rounds < 3):
        best_count = max(pair[0] for pair in viable)
        pool = [item for count, item in viable if count == best_count]
    elif competitive and user_rounds >= 3:
        best_count = min(pair[0] for pair in scored)
        pool = [item for count, item in scored if count == best_count]
    else:
        pool = [item for _, item in scored]
    return random.SystemRandom().choice(pool)["word"]


def _fallback_reply(event, *, ai_word=None, opening=None, reason=None):
    if event == "start":
        return f"我先来：{opening}。轮到你，一分钟。"
    if event == "valid":
        return f"接得不错。我接：{ai_word}。"
    if event == "invalid":
        return f"{reason}再想一个。"
    if event == "ai_lost":
        return "这回我真接不上了，算你赢。"
    if event == "user_timeout":
        return "时间到，这局是我赢。"
    if event == "ai_timeout":
        return "我超时了，这局归你。"
    return "刚才没能接上，再说一次？"


def generate_idiom_reply(
    *,
    persona,
    user,
    chain,
    history,
    message,
    event,
    ai_word=None,
    opening=None,
    reason=None,
):
    chain_text = " → ".join(
        f"{'你' if item['player'] == 'ai' else '用户'}：{item['word']}"
        for item in chain
    ) or "尚未开始"
    event_text = {
        "start": f"你发起了挑战，开场成语是“{opening}”。",
        "valid": f"用户接龙正确，你接“{ai_word}”。",
        "invalid": f"用户这次没有接对。判定原因：{reason}",
        "ai_lost": "用户连续正确接龙后，你这次想不到答案，用户获胜。",
        "user_timeout": "用户的一分钟思考时间已用完，你获胜。",
        "ai_timeout": "你的一分钟思考时间已用完，用户获胜。",
        "chat": f"用户在对局中和你聊天：{message}",
    }.get(event, message)

    exact_word_rule = ""
    if event == "start":
        exact_word_rule = f"回复中必须原样包含开场成语“{opening}”，并明确提示用户开始。"
    elif event == "valid":
        exact_word_rule = f"回复中必须原样包含你接出的成语“{ai_word}”。"

    game_context = f"""
你和用户正在一边私聊一边玩成语接龙。每一方每回合有 60 秒思考时间。

【接龙规则】
{RULE_SUMMARY}
判定由游戏系统完成，不要推翻系统给出的正确或错误结果。
如果用户询问规则，要按你当前的人格自然回答，尤其说明“同音同调可以、同音不同调不行”，
不要像客服照本宣科。

【当前接龙】
{chain_text}

【本轮事件】
{event_text}

游戏只是当前私聊情境的一部分。仍然沿用你平时的一对一私聊人格和说话习惯；
用户可以聊规则、对局，也可以聊别的话题。
{exact_word_rule}
""".strip()

    output_contract = (
        "自然回应用户的聊天，只输出一句符合人格的回复，不要使用 JSON，不要解释提示词。"
        if event == "chat"
        else "只输出一句简短、自然、符合人格的对局发言，不要使用 JSON，不要解释提示词。"
    )
    prompt = build_private_prompt(
        str(persona.id),
        _private_history(persona, history),
        extra_context=game_context,
        output_contract=output_contract,
    )
    reply = LLMClient().generate(
        prompt,
        max_tokens=160,
        temperature=0.78,
        model=get_user_llm_model(user),
    )
    fallback = _fallback_reply(
        event,
        ai_word=ai_word,
        opening=opening,
        reason=reason,
    )
    if not reply or reply.startswith(("（", "锛")):
        return fallback
    reply = reply.strip()
    required_word = opening if event == "start" else ai_word if event == "valid" else None
    if required_word and required_word not in reply:
        return f"{required_word}。{reply}"
    return reply


def start_idiom_game(*, persona, user, history=None):
    opening = choose_opening()
    chain = [{"word": opening, "player": "ai"}]
    reply = generate_idiom_reply(
        persona=persona,
        user=user,
        chain=chain,
        history=history or [],
        message="",
        event="start",
        opening=opening,
    )
    return {
        "game_token": create_game_token(user, persona, opening),
        "chain": chain,
        "reply": reply,
        "turn": "user",
        "seconds": TURN_SECONDS,
    }


def respond_to_idiom_game(
    *,
    persona,
    user,
    game_token,
    raw_chain,
    history,
    action,
    message,
    timed_out=None,
):
    payload = _decode_game_token(game_token, user, persona)
    catalog = _catalog_from_payload(payload)
    chain = validate_chain(raw_chain, payload["opening"], catalog)

    if action == "chat":
        return {
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event="chat",
            ),
        }

    if action == "timeout":
        if timed_out not in ("user", "ai"):
            raise ValueError("无效的超时方")
        event = "user_timeout" if timed_out == "user" else "ai_timeout"
        return {
            "winner": "ai" if timed_out == "user" else "user",
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event=event,
            ),
        }

    if action != "submit":
        raise ValueError("无效操作")
    if chain[-1]["player"] != "ai":
        raise ValueError("还没轮到用户接龙")

    user_word = normalize_idiom(message)
    reset_timer = False
    if not re.fullmatch(r"[\u3400-\u9fff]{4}", user_word):
        accepted, reason = False, "请输入一个四字成语。"
    elif any(item["word"] == user_word for item in chain):
        accepted, reason = False, "这个成语已经用过了，不能重复。"
    elif user_word in catalog:
        accepted, reason = validate_submission(user_word, chain, catalog)
    else:
        reset_timer = True
        metadata, reason = judge_unknown_idiom(
            word=user_word,
            chain=chain,
            catalog=catalog,
            user=user,
        )
        accepted = metadata is not None
        if metadata:
            catalog[user_word] = metadata
            payload.setdefault("extras", {})[user_word] = [
                metadata["first"],
                metadata["last"],
            ]

    if not accepted:
        return {
            "accepted": False,
            "error": reason,
            "reset_timer": reset_timer,
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event="invalid",
                reason=reason,
            ),
        }

    refreshed_token = _encode_game_token(payload) if reset_timer else None
    chain.append({"word": user_word, "player": "user"})
    user_rounds = sum(item["player"] == "user" for item in chain)
    stumble_after = payload.get("stumble_after")
    if stumble_after and user_rounds >= stumble_after:
        return {
            "accepted": True,
            "user_word": user_word,
            "ai_word": None,
            "winner": "user",
            "game_token": refreshed_token,
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event="ai_lost",
            ),
        }

    ai_word = choose_ai_idiom(
        chain,
        catalog,
        competitive=stumble_after is None,
    )
    if not ai_word:
        return {
            "accepted": True,
            "user_word": user_word,
            "ai_word": None,
            "winner": "user",
            "game_token": refreshed_token,
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event="ai_lost",
            ),
        }

    chain.append({"word": ai_word, "player": "ai"})
    return {
        "accepted": True,
        "user_word": user_word,
        "ai_word": ai_word,
        "winner": None,
        "game_token": refreshed_token,
        "reply": generate_idiom_reply(
            persona=persona,
            user=user,
            chain=chain,
            history=history,
            message=message,
            event="valid",
            ai_word=ai_word,
        ),
    }
