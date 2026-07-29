import random
import secrets

from django.core import signing

from apps.dialogue.services.llm_client import LLMClient
from apps.dialogue.services.private_prompt_builder import build_private_prompt
from apps.users.services.model_selection import get_user_llm_model

from .idiom_data import IDIOMS, OPENING_IDIOMS


GAME_TOKEN_SALT = "what-ai.idiom-game.v1"
MAX_CHAIN_LENGTH = 80
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


def validate_chain(raw_chain, opening):
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
        if player != expected_player or word not in IDIOMS or word in used:
            raise ValueError("对局记录无效")
        if index == 0 and word != opening:
            raise ValueError("对局开场不一致")
        if previous and not same_syllable_and_tone(
            IDIOMS[previous]["last"],
            IDIOMS[word]["first"],
        ):
            raise ValueError("对局接龙关系无效")
        chain.append({"word": word, "player": player})
        used.add(word)
        previous = word
    return chain


def validate_submission(word, chain):
    word = normalize_idiom(word)
    if len(word) != 4:
        return False, "请输入一个四字成语。"
    if word not in IDIOMS:
        return False, "这个成语不在本局常用词库里，换一个试试。"
    if any(item["word"] == word for item in chain):
        return False, "这个成语已经用过了，不能重复。"

    previous = chain[-1]["word"]
    expected = IDIOMS[previous]["last"]
    actual = IDIOMS[word]["first"]
    if not same_syllable_and_tone(expected, actual):
        return False, (
            f"“{word[0]}”和“{previous[-1]}”不是同音同调，"
            "这次接不上。"
        )
    return True, ""


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
    return payload


def create_game_token(user, persona, opening):
    # About 45% of matches give the player a reachable AI stumble after
    # several genuinely correct answers. The rest keep the AI competitive.
    stumble_after = (
        random.SystemRandom().choice((3, 4, 4, 5, 5, 6))
        if random.SystemRandom().random() < 0.45
        else None
    )
    return signing.dumps(
        {
            "user_id": user.id,
            "persona_id": persona.id,
            "opening": opening,
            "stumble_after": stumble_after,
            "nonce": secrets.token_urlsafe(8),
        },
        salt=GAME_TOKEN_SALT,
        compress=True,
    )


def choose_opening():
    return random.SystemRandom().choice(OPENING_IDIOMS)


def choose_ai_idiom(chain, competitive=False):
    used = {item["word"] for item in chain}
    required = IDIOMS[chain[-1]["word"]]["last"]
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
        return f"我先来：{opening}。轮到你，三十秒。"
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
        "user_timeout": "用户的三十秒思考时间已用完，你获胜。",
        "ai_timeout": "你的三十秒思考时间已用完，用户获胜。",
        "chat": f"用户在对局中和你聊天：{message}",
    }.get(event, message)

    exact_word_rule = ""
    if event == "start":
        exact_word_rule = f"回复中必须原样包含开场成语“{opening}”，并明确提示用户开始。"
    elif event == "valid":
        exact_word_rule = f"回复中必须原样包含你接出的成语“{ai_word}”。"

    game_context = f"""
你和用户正在一边私聊一边玩成语接龙。每一方每回合有 30 秒思考时间。

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
        "seconds": 30,
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
    chain = validate_chain(raw_chain, payload["opening"])

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

    accepted, reason = validate_submission(message, chain)
    if not accepted:
        return {
            "accepted": False,
            "error": reason,
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

    user_word = normalize_idiom(message)
    chain.append({"word": user_word, "player": "user"})
    user_rounds = sum(item["player"] == "user" for item in chain)
    stumble_after = payload.get("stumble_after")
    if stumble_after and user_rounds >= stumble_after:
        return {
            "accepted": True,
            "user_word": user_word,
            "ai_word": None,
            "winner": "user",
            "reply": generate_idiom_reply(
                persona=persona,
                user=user,
                chain=chain,
                history=history,
                message=message,
                event="ai_lost",
            ),
        }

    ai_word = choose_ai_idiom(chain, competitive=stumble_after is None)
    if not ai_word:
        return {
            "accepted": True,
            "user_word": user_word,
            "ai_word": None,
            "winner": "user",
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
