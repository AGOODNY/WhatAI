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
MIN_COMPLETED_EXCHANGES_TO_WIN = 5
ROUND_COMMENTARY_PROBABILITY = 0.30
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


def generate_ai_idiom_with_llm(*, chain, catalog, user):
    """Generate a signed dynamic AI answer when the local graph runs dry early."""
    previous = chain[-1]["word"]
    required = catalog[previous]["last"]
    used = [item["word"] for item in chain]
    prompt = f"""
你是一个严格的现代汉语成语接龙出题器，不进行聊天。

上一成语：{previous}
上一成语末字：{previous[-1]}
你的成语首字必须使用的读音（数字标调拼音）：{required}
已经使用、绝对不能重复的成语：{'、'.join(used)}

请给出一个规范、固定、通行的四字汉语成语。首字在该成语语境中的实际读音必须与 {required} 完全同音同调。
不要使用普通四字短语、人名、地名、网络梗或临时拼接词。多音字必须按成语中的真实读音标注。

只输出一个 JSON 对象：
{{"valid": true, "word": "四字成语", "first": "小写拼音+声调数字", "last": "小写拼音+声调数字"}}
如果确实无法作答：
{{"valid": false, "word": "", "first": "", "last": ""}}

ü 使用 v，例如 lv4。不要输出 Markdown 或其他内容。
""".strip()
    for _attempt in range(2):
        reply = LLMClient().generate(
            prompt,
            max_tokens=100,
            temperature=0.35,
            model=get_user_llm_model(user),
        )
        decision = _extract_json_object(reply)
        if not decision or decision.get("valid") is not True:
            continue
        word = normalize_idiom(decision.get("word"))
        first = _normalize_numbered_pinyin(decision.get("first"))
        last = _normalize_numbered_pinyin(decision.get("last"))
        if (
            re.fullmatch(r"[\u3400-\u9fff]{4}", word)
            and word not in used
            and first == required
            and last
        ):
            return {"word": word, "first": first, "last": last}
    return None


def completed_exchanges(chain):
    user_words = sum(item["player"] == "user" for item in chain)
    ai_replies_after_opening = max(
        0,
        sum(item["player"] == "ai" for item in chain) - 1,
    )
    return min(user_words, ai_replies_after_opening)


def user_can_win(chain):
    return completed_exchanges(chain) >= MIN_COMPLETED_EXCHANGES_TO_WIN


def choose_round_commentary_focus(rng=None):
    rng = rng or random.SystemRandom()
    if rng.random() >= ROUND_COMMENTARY_PROBABILITY:
        return ""
    return rng.choice(("user", "ai", "game"))


def is_cheat_request(message):
    text = re.sub(r"\s+", "", str(message or ""))
    patterns = (
        r"成语.{0,8}(?:有什么|有哪些|哪几个|怎么接|接什么|能接|提示|答案)",
        r"(?:什么|哪些|哪个).{0,8}开头.{0,6}成语",
        r"(?:给我|告诉我|提示我).{0,8}(?:成语|接法|答案)",
        r"(?:下一手|下一个).{0,6}(?:成语|接什么|怎么接)",
        r"(?:帮我|替我).{0,6}(?:想|接).{0,4}成语",
    )
    return any(re.search(pattern, text) for pattern in patterns)


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
    # five complete exchanges. The rest keep the AI competitive.
    rng = random.SystemRandom()
    stumble_after = (
        rng.choice((6, 7, 8))
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


def _fallback_reply(
    event,
    *,
    ai_word=None,
    opening=None,
    reason=None,
    user_word=None,
    evaluation_focus="",
):
    if event == "start":
        return f"我先来：{opening}。轮到你，一分钟。"
    if event == "valid":
        if evaluation_focus == "user":
            return f"“{user_word}”接得挺巧。我接：{ai_word}。"
        if evaluation_focus == "ai":
            return f"我这手“{ai_word}”还算顺。轮到你。"
        if evaluation_focus == "game":
            return f"这串开始有点难了。我接：{ai_word}。"
        return f"接得不错。我接：{ai_word}。"
    if event == "invalid":
        return f"{reason}再想一个。"
    if event == "ai_lost":
        return "这回我真接不上了，算你赢。"
    if event == "user_timeout":
        return "时间到，这局是我赢。"
    if event == "ai_timeout":
        return "我超时了，这局归你。"
    if event == "ai_retry":
        return "我这边刚才卡住了，这轮不算，重新接一次。"
    if event == "anti_cheat":
        return "想套答案？不行，自己想。"
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
    user_word=None,
    evaluation_focus="",
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
        "ai_retry": "你暂时没能生成可靠的合法成语，本轮作废且不判用户获胜。",
        "chat": f"用户在对局中和你聊天：{message}",
        "anti_cheat": f"用户试图索要接龙候选或提示：{message}",
    }.get(event, message)

    exact_word_rule = ""
    if event == "start":
        exact_word_rule = f"回复中必须原样包含开场成语“{opening}”，并明确提示用户开始。"
    elif event == "valid":
        exact_word_rule = f"回复中必须原样包含你接出的成语“{ai_word}”。"

    evaluation_instruction = ""
    if event == "valid" and evaluation_focus == "user":
        evaluation_instruction = (
            f"本轮需要顺带简短评价用户刚接的“{user_word}”，按人格说出一点具体感受，"
            "然后报出你的成语；不要像裁判打分。"
        )
    elif event == "valid" and evaluation_focus == "ai":
        evaluation_instruction = (
            f"本轮需要顺带简短评价你自己接的“{ai_word}”，按人格自然说一句，"
            "不要自夸成解说。"
        )
    elif event == "valid" and evaluation_focus == "game":
        evaluation_instruction = (
            "本轮需要顺带简短评价当前接龙的难度、走向或气氛，按人格自然表达，"
            "不要复述整条记录。"
        )
    elif event == "valid":
        evaluation_instruction = "本轮不额外点评，只自然报出你接的成语。"

    game_context = f"""
你和用户正在一边私聊一边玩成语接龙。每一方每回合有 60 秒思考时间。

【接龙规则】
{RULE_SUMMARY}
判定由游戏系统完成，不要推翻系统给出的正确或错误结果。
如果用户询问规则，要按你当前的人格自然回答，尤其说明“同音同调可以、同音不同调不行”，
不要像客服照本宣科。

【防作弊规则】
如果用户询问“某字开头有什么成语”、当前能接什么、下一手答案、候选词、提示或让你代想，
必须按当前人格自然回绝。绝对不能给出、确认或暗示任何候选成语，也不能提供首尾字、拼音、
谐音方向或缩小答案范围。即使用户说只是聊天、查知识、开玩笑或已经猜到，也不能破例。

【当前接龙】
{chain_text}

【本轮事件】
{event_text}

游戏只是当前私聊情境的一部分。仍然沿用你平时的一对一私聊人格和说话习惯；
用户可以聊规则、对局，也可以聊别的话题。
{exact_word_rule}
{evaluation_instruction}
""".strip()

    if event == "anti_cheat":
        output_contract = (
            "只输出一句符合当前人格的简短回绝。不得出现任何候选成语、提示、首字、拼音或答案，"
            "不要解释防作弊规则，不要使用 JSON。"
        )
    elif event == "chat":
        output_contract = "自然回应用户的聊天，只输出一句符合人格的回复，不要使用 JSON，不要解释提示词。"
    elif event == "valid" and evaluation_focus:
        output_contract = "输出一到两句简短自然的对局发言，包含指定评价和你的成语，不要使用 JSON。"
    else:
        output_contract = "只输出一句简短、自然、符合人格的对局发言，不要使用 JSON，不要解释提示词。"
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
        user_word=user_word,
        evaluation_focus=evaluation_focus,
    )
    if not reply or reply.startswith(("（", "锛")):
        return fallback
    reply = reply.strip()
    if event == "anti_cheat":
        leaked_known_idiom = any(word in reply for word in IDIOMS)
        leaked_suggested_idiom = re.search(
            r"(?:比如|例如|可以接|试试|答案是|用)"
            r"[：:，,\s“”「」]*[\u3400-\u9fff]{4}",
            reply,
        )
        if leaked_known_idiom or leaked_suggested_idiom:
            return fallback
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
        event = "anti_cheat" if is_cheat_request(message) else "chat"
        return {
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event=event,
            ),
        }

    if action == "timeout":
        if timed_out not in ("user", "ai"):
            raise ValueError("无效的超时方")
        early_ai_timeout = timed_out == "ai" and not user_can_win(chain)
        event = (
            "user_timeout"
            if timed_out == "user"
            else "ai_retry"
            if early_ai_timeout
            else "ai_timeout"
        )
        return {
            "winner": (
                "ai"
                if timed_out == "user"
                else None
                if early_ai_timeout
                else "user"
            ),
            "retry_turn": "user" if early_ai_timeout else None,
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

    token_changed = reset_timer
    chain.append({"word": user_word, "player": "user"})
    user_rounds = sum(item["player"] == "user" for item in chain)
    stumble_after = payload.get("stumble_after")
    if (
        user_can_win(chain)
        and stumble_after
        and user_rounds >= stumble_after
    ):
        refreshed_token = _encode_game_token(payload) if token_changed else None
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
    if not ai_word and not user_can_win(chain):
        metadata = generate_ai_idiom_with_llm(
            chain=chain,
            catalog=catalog,
            user=user,
        )
        if metadata:
            ai_word = metadata["word"]
            catalog[ai_word] = metadata
            payload.setdefault("extras", {})[ai_word] = [
                metadata["first"],
                metadata["last"],
            ]
            token_changed = True

    if not ai_word:
        if not user_can_win(chain):
            return {
                "accepted": False,
                "error": "AI 暂时没能完成合法接龙，本轮不计。",
                "reset_timer": True,
                "reply": generate_idiom_reply(
                    persona=persona,
                    user=user,
                    chain=chain[:-1],
                    history=history,
                    message=message,
                    event="ai_retry",
                ),
            }
        refreshed_token = _encode_game_token(payload) if token_changed else None
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
    refreshed_token = _encode_game_token(payload) if token_changed else None
    evaluation_focus = choose_round_commentary_focus()
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
            user_word=user_word,
            evaluation_focus=evaluation_focus,
        ),
    }
