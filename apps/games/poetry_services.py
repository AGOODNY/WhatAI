import json
import random
import re
import secrets

from django.core import signing

from apps.dialogue.services.llm_client import LLMClient
from apps.dialogue.services.private_prompt_builder import build_private_prompt
from apps.users.services.model_selection import get_user_llm_model

from .poetry_data import PLAYABLE_TARGETS, POETRY_LINES


GAME_TOKEN_SALT = "what-ai.poetry-game.v1"
TURN_SECONDS = 120
MIN_USER_ANSWERS_TO_WIN = 6
ROUND_COMMENTARY_PROBABILITY = 0.30
MAX_VERSES = 80


def normalize_verse(value):
    text = str(value or "").strip()
    text = text.strip("“”「」『』")
    text = text.replace(",", "，").replace(";", "；")
    text = re.sub(r"\s*([，；])\s*", r"\1", text)
    text = re.sub(r"\s+", "，", text)
    return text.rstrip("。！？!?")


def is_complete_sentence_shape(verse):
    parts = re.split(r"[，；]", verse)
    return (
        len(parts) >= 2
        and all(3 <= len(re.findall(r"[\u3400-\u9fff]", part)) <= 12 for part in parts)
        and all(re.fullmatch(r"[\u3400-\u9fff]+", part) for part in parts)
    )


def _extract_json_object(text):
    text = (text or "").strip()
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


def _private_history(persona, history):
    persona_token = str(persona.id)
    result = []
    for item in history[-24:] if isinstance(history, list) else []:
        if not isinstance(item, dict):
            continue
        result.append({
            "role": "USER" if item.get("role") == "user" else persona_token,
            "content": str(item.get("content", ""))[:500],
        })
    return result


def _new_payload(user, persona):
    rng = random.SystemRandom()
    return {
        "user_id": user.id,
        "persona_id": persona.id,
        "phase": "choose_side",
        "target": "",
        "verses": [],
        # Only about one quarter of matches have a planned, reachable stumble.
        # It can never happen before the player's sixth correct answer.
        "stumble_after": rng.choice((6, 7)) if rng.random() < 0.25 else None,
        "nonce": secrets.token_urlsafe(8),
    }


def _encode_game_token(payload):
    return signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)


def create_game_token(user, persona):
    return _encode_game_token(_new_payload(user, persona))


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
        or payload.get("phase") not in ("choose_side", "choose_character", "playing", "finished")
        or not isinstance(payload.get("verses"), list)
    ):
        raise ValueError("对局凭证无效")
    return payload


def _validate_client_verses(raw_verses, payload):
    if raw_verses is None:
        raw_verses = []
    if not isinstance(raw_verses, list) or len(raw_verses) > MAX_VERSES:
        raise ValueError("诗词记录无效")
    cleaned = []
    for item in raw_verses:
        if not isinstance(item, dict) or item.get("player") not in ("user", "ai"):
            raise ValueError("诗词记录无效")
        cleaned.append({
            "verse": normalize_verse(item.get("verse")),
            "player": item["player"],
        })
    if cleaned != payload["verses"]:
        raise ValueError("诗词记录与当前对局不一致")
    return cleaned


def choose_target():
    return random.SystemRandom().choice(PLAYABLE_TARGETS)


def _known_candidates(target, used):
    return [line for line in POETRY_LINES if target in line and line not in used]


def _generate_ai_verse(target, used, user):
    known = _known_candidates(target, used)
    if known:
        return random.SystemRandom().choice(known)

    prompt = f"""
你是严格的中国古典诗词检索器，不进行聊天。
请给出一句真实存在、可以核实的中国古典诗词或古典词曲原句，必须满足：
1. 原句包含“{target}”字；
2. 必须是一个完整句子，至少包含由逗号或分号连接的上下两部分；
3. 不得是现代诗、网络仿作、改写或自行创作；
4. 不得与以下已用句子重复：{json.dumps(sorted(used), ensure_ascii=False)}。
只输出 JSON：{{"verse":"完整原句"}}。找不到时输出 {{"verse":""}}。
""".strip()
    for _ in range(2):
        decision = _extract_json_object(LLMClient().generate(
            prompt,
            max_tokens=100,
            temperature=0.15,
            model=get_user_llm_model(user),
        ))
        verse = normalize_verse(decision.get("verse")) if decision else ""
        if (
            verse
            and target in verse
            and verse not in used
            and is_complete_sentence_shape(verse)
        ):
            return verse
    return None


def _judge_unknown_verse(verse, target, user):
    prompt = f"""
你是严格的中国古典诗词裁判，不进行聊天。判断用户输入是否为真实存在的古典诗、词或曲中的完整一句。
目标字：“{target}”
用户输入：“{verse}”

判定标准：
- 必须原样包含目标字；
- 必须是完整句子，通常有上下两部分；只写“床前明月光”这种半句不合格，
  “床前明月光，疑是地上霜”才合格；
- 只接受中国古典诗词曲，不接受现代诗、网络句子、改写、拼接、杜撰；
- 可修正明显的常见标点差异，但不得替用户补写缺失的半句。
只输出 JSON：
{{"valid":true,"canonical":"规范完整原句","reason":""}}
或 {{"valid":false,"canonical":"","reason":"温和、简短的中文原因"}}。
""".strip()
    decision = _extract_json_object(LLMClient().generate(
        prompt,
        max_tokens=150,
        temperature=0.0,
        model=get_user_llm_model(user),
    ))
    if not decision or decision.get("valid") is not True:
        reason = str((decision or {}).get("reason") or "这句暂时无法确认为完整的古典诗词。")
        return None, reason[:80]
    canonical = normalize_verse(decision.get("canonical"))
    if target not in canonical or not is_complete_sentence_shape(canonical):
        return None, "请说出包含目标字的完整古典诗词句子。"
    return canonical, ""


def is_cheat_request(message, target=""):
    text = re.sub(r"\s+", "", str(message or ""))
    quoted_target = re.escape(target) if target else r"[\u3400-\u9fff]"
    patterns = (
        rf"(?:含|带|有).{{0,3}}{quoted_target}.{{0,5}}(?:诗|词|句).{{0,5}}(?:有哪些|有什么|举例|告诉|提示)",
        rf"(?:哪些|什么).{{0,6}}(?:诗|词|句).{{0,5}}(?:含|带|有).{{0,3}}{quoted_target}",
        r"(?:下一句|下一个).{0,5}(?:说什么|怎么接|答案|提示)",
        r"(?:帮我|替我).{0,5}(?:想|找|说).{0,4}(?:诗|词|句)",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _fallback_reply(event, *, target="", ai_verse="", reason="", user_verse=""):
    replies = {
        "choose_side": "这一局，字由我来选，还是你来选？",
        "choose_character": "好，你来选。输入一个想用的字吧。",
        "invalid_character": "请只输入一个汉字；这个字得让我们有诗可接。",
        "ai_choose_start": f"我选{target}字。我先来：{ai_verse}",
        "start": f"那就以“{target}”为令。我先来：{ai_verse}",
        "valid": f"这句算。我的下一句是：{ai_verse}",
        "invalid": f"{reason} 再想一句也不迟。",
        "ai_lost": "这一回我确实想不到新的句子了，你赢。",
        "user_timeout": "两分钟到了，这局就算我险胜。",
        "ai_timeout": "我想得太久了，这局归你。",
        "ai_retry": "我一时没找到可靠的原句，这轮先不算，你再来一次。",
        "anti_cheat": "这可不能替你报答案，慢慢想，我等你。",
        "chat": "我在听。",
    }
    return replies.get(event, "再试一次？")


def generate_poetry_reply(
    *,
    persona,
    user,
    verses,
    history,
    message,
    event,
    target="",
    ai_verse="",
    user_verse="",
    reason="",
    add_commentary=False,
):
    verse_text = "\n".join(
        f"{'你' if item['player'] == 'ai' else '用户'}：{item['verse']}"
        for item in verses[-16:]
    ) or "尚未开始"
    event_text = {
        "choose_side": "你要先询问用户：这一局由你选字，还是用户选字。",
        "choose_character": "用户表示要自己选字，请提示他输入一个汉字。",
        "invalid_character": f"用户给的选字暂时不能开局：{reason}",
        "ai_choose_start": f"你选定“{target}”字，并用“{ai_verse}”开场。",
        "start": f"目标字已定为“{target}”，你用“{ai_verse}”开场。",
        "valid": f"用户用“{user_verse}”正确应答；你接“{ai_verse}”。",
        "invalid": f"用户的应答不合规：{reason}",
        "ai_lost": "用户已达到获胜门槛，你自然词穷，用户获胜。",
        "user_timeout": "用户两分钟超时，你获胜。",
        "ai_timeout": "你两分钟超时，用户获胜。",
        "ai_retry": "系统未找到可靠的古典原句，本轮不计分。",
        "chat": f"用户在对局中和你聊天：{message}",
        "anti_cheat": f"用户试图索要含目标字的诗词答案或提示：{message}",
    }.get(event, message)

    exact_rule = ""
    if event == "ai_choose_start":
        exact_rule = (
            f"回复必须先原样说“我选{target}字”，然后再原样说出开场诗句“{ai_verse}”。"
        )
    elif event in ("start", "valid"):
        exact_rule = f"回复必须原样包含你本轮说出的诗句“{ai_verse}”。"
    commentary_rule = (
        f"本轮还要顺带自然聊一句对用户诗句“{user_verse}”的理解、画面或感受，"
        "要具体但简短，不要像教材赏析。"
        if event == "valid" and add_commentary
        else "本轮只完成对答，不额外点评。"
        if event == "valid"
        else ""
    )
    game_context = f"""
你和用户正在一边私聊一边玩飞花令，每一方每回合有 2 分钟思考时间。

【规则】
双方轮流说一句含目标字的中国古典诗词曲原句。必须是整句：
“床前明月光，疑是地上霜”合规，只说“床前明月光”不合规。
现代诗、改写、杜撰和已经说过的句子都不合规。系统判定不可推翻。

【防作弊】
如果用户询问含某字的诗词有哪些、索要候选、答案、下一句或提示，必须按当前人格温和而自然地拒绝。
绝对不能给出、确认或暗示任何可用诗句，也不要用首字、作者、篇名等缩小范围。

【目标字】{target or "尚未确定"}
【当前诗句】
{verse_text}
【本轮事件】
{event_text}

游戏只是当前一对一私聊的情境。继续使用你平时的私聊人格、语气和关系感，不要变成主持人或客服。
{exact_rule}
{commentary_rule}
""".strip()
    if event == "anti_cheat":
        contract = "只输出一句符合人格的温和回绝，不得包含任何候选诗句、作者、篇名或提示。"
    elif event == "chat":
        contract = "自然回应用户的聊天，只输出简短、符合人格的私聊回复。"
    elif event == "valid" and add_commentary:
        contract = "输出一到两句自然对局发言，包含简短感受和指定诗句。"
    else:
        contract = "只输出一句简短、自然、符合人格的对局发言。"
    prompt = build_private_prompt(
        str(persona.id),
        _private_history(persona, history),
        extra_context=game_context,
        output_contract=contract,
    )
    reply = LLMClient().generate(
        prompt,
        max_tokens=180,
        temperature=0.76,
        model=get_user_llm_model(user),
    )
    fallback = _fallback_reply(
        event,
        target=target,
        ai_verse=ai_verse,
        reason=reason,
        user_verse=user_verse,
    )
    if not reply or reply.startswith(("（", "锛")):
        return fallback
    reply = reply.strip()
    if event == "anti_cheat":
        # A refusal must not accidentally leak a playable line.
        if any(line in reply for line in POETRY_LINES) or re.search(r"[，；].{3,}", reply):
            return fallback
    if event == "ai_choose_start" and f"我选{target}字" not in reply:
        reply = f"我选{target}字。{reply}"
    if ai_verse and ai_verse not in reply:
        return f"{reply} {ai_verse}"
    return reply


def _start_with_target(payload, target, user):
    opening = _generate_ai_verse(target, set(), user)
    if not opening:
        return None
    payload["phase"] = "playing"
    payload["target"] = target
    payload["verses"] = [{"verse": opening, "player": "ai"}]
    return opening


def start_poetry_game(*, persona, user, history=None):
    payload = _new_payload(user, persona)
    return {
        "game_token": _encode_game_token(payload),
        "phase": payload["phase"],
        "target": "",
        "verses": [],
        "reply": generate_poetry_reply(
            persona=persona,
            user=user,
            verses=[],
            history=history or [],
            message="",
            event="choose_side",
        ),
        "turn": "choosing",
        "seconds": TURN_SECONDS,
    }


def _choose_side_from_message(message):
    text = re.sub(r"\s+", "", str(message or ""))
    if re.search(r"(?:我|玩家|自己)(?:来)?选(?:字)?|我选字", text):
        return "user"
    if re.search(r"(?:你|AI|ai)(?:来)?选(?:字)?|你选字|随便", text, re.I):
        return "ai"
    return ""


def respond_to_poetry_game(
    *,
    persona,
    user,
    game_token,
    raw_verses,
    history,
    action,
    message,
    timed_out=None,
):
    payload = _decode_game_token(game_token, user, persona)
    verses = _validate_client_verses(raw_verses, payload)
    phase = payload["phase"]

    if action == "chat":
        event = "anti_cheat" if is_cheat_request(message, payload["target"]) else "chat"
        return {
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event=event,
                target=payload["target"],
            ),
        }

    if phase == "choose_side":
        choice = _choose_side_from_message(message)
        if not choice:
            return {
                "accepted": False,
                "phase": phase,
                "reply": generate_poetry_reply(
                    persona=persona,
                    user=user,
                    verses=[],
                    history=history,
                    message=message,
                    event="choose_side",
                ),
            }
        if choice == "user":
            payload["phase"] = "choose_character"
            return {
                "accepted": True,
                "phase": payload["phase"],
                "game_token": _encode_game_token(payload),
                "reply": generate_poetry_reply(
                    persona=persona,
                    user=user,
                    verses=[],
                    history=history,
                    message=message,
                    event="choose_character",
                ),
                "turn": "choosing",
            }
        target = choose_target()
        opening = _start_with_target(payload, target, user)
        return {
            "accepted": True,
            "phase": payload["phase"],
            "target": target,
            "ai_verse": opening,
            "verses": payload["verses"],
            "game_token": _encode_game_token(payload),
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=payload["verses"],
                history=history,
                message=message,
                event="ai_choose_start",
                target=target,
                ai_verse=opening,
            ),
            "turn": "user",
        }

    if phase == "choose_character":
        target = re.sub(r"\s+", "", str(message or ""))
        if not re.fullmatch(r"[\u3400-\u9fff]", target):
            reason = "请只输入一个汉字。"
            return {
                "accepted": False,
                "phase": phase,
                "error": reason,
                "reply": generate_poetry_reply(
                    persona=persona,
                    user=user,
                    verses=[],
                    history=history,
                    message=message,
                    event="invalid_character",
                    reason=reason,
                ),
            }
        opening = _start_with_target(payload, target, user)
        if not opening:
            reason = "这个字暂时找不到可靠的开场诗句，换一个字试试吧。"
            return {
                "accepted": False,
                "phase": phase,
                "error": reason,
                "reply": generate_poetry_reply(
                    persona=persona,
                    user=user,
                    verses=[],
                    history=history,
                    message=message,
                    event="invalid_character",
                    reason=reason,
                ),
            }
        return {
            "accepted": True,
            "phase": payload["phase"],
            "target": target,
            "ai_verse": opening,
            "verses": payload["verses"],
            "game_token": _encode_game_token(payload),
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=payload["verses"],
                history=history,
                message=message,
                event="start",
                target=target,
                ai_verse=opening,
            ),
            "turn": "user",
        }

    if phase not in ("playing", "finished"):
        raise ValueError("对局状态无效")
    target = payload["target"]

    if action == "timeout":
        if timed_out not in ("user", "ai"):
            raise ValueError("无效的超时方")
        user_answers = sum(item["player"] == "user" for item in verses)
        early_ai_timeout = timed_out == "ai" and user_answers < MIN_USER_ANSWERS_TO_WIN
        event = "user_timeout" if timed_out == "user" else "ai_retry" if early_ai_timeout else "ai_timeout"
        if not early_ai_timeout:
            payload["phase"] = "finished"
        return {
            "winner": "ai" if timed_out == "user" else None if early_ai_timeout else "user",
            "retry_turn": "user" if early_ai_timeout else None,
            "game_token": _encode_game_token(payload),
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event=event,
                target=target,
            ),
        }

    if action not in ("submit", "smart"):
        raise ValueError("无效操作")
    if phase == "finished":
        raise ValueError("本局已经结束")
    if not verses or verses[-1]["player"] != "ai":
        raise ValueError("还没轮到用户作答")

    user_verse = normalize_verse(message)
    if is_cheat_request(message, target) and action == "smart":
        return {
            "routed_action": "chat",
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event="anti_cheat",
                target=target,
            ),
        }
    if target not in user_verse:
        accepted, reason = False, f"这句里没有“{target}”字。"
    elif not is_complete_sentence_shape(user_verse):
        accepted, reason = False, "要说完整的一句，上下句都要有。"
    elif user_verse in {item["verse"] for item in verses}:
        accepted, reason = False, "这句已经说过了，换一句吧。"
    elif user_verse in POETRY_LINES:
        accepted, reason = True, ""
    else:
        canonical, reason = _judge_unknown_verse(user_verse, target, user)
        accepted = canonical is not None
        if canonical:
            user_verse = canonical
            if user_verse in {item["verse"] for item in verses}:
                accepted, reason = False, "这句已经说过了，换一句吧。"
    if not accepted:
        return {
            "accepted": False,
            "error": reason,
            "reset_timer": user_verse not in POETRY_LINES,
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event="invalid",
                target=target,
                reason=reason,
            ),
        }

    verses.append({"verse": user_verse, "player": "user"})
    payload["verses"] = verses
    user_answers = sum(item["player"] == "user" for item in verses)
    if payload.get("stumble_after") and user_answers >= payload["stumble_after"]:
        payload["phase"] = "finished"
        return {
            "accepted": True,
            "user_verse": user_verse,
            "ai_verse": None,
            "winner": "user",
            "game_token": _encode_game_token(payload),
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event="ai_lost",
                target=target,
            ),
        }

    ai_verse = _generate_ai_verse(
        target,
        {item["verse"] for item in verses},
        user,
    )
    if not ai_verse:
        if user_answers < MIN_USER_ANSWERS_TO_WIN:
            verses.pop()
            payload["verses"] = verses
            return {
                "accepted": False,
                "error": "AI 暂时没找到可靠的完整原句，本轮不计。",
                "reset_timer": True,
                "game_token": _encode_game_token(payload),
                "reply": generate_poetry_reply(
                    persona=persona,
                    user=user,
                    verses=verses,
                    history=history,
                    message=message,
                    event="ai_retry",
                    target=target,
                ),
            }
        payload["phase"] = "finished"
        return {
            "accepted": True,
            "user_verse": user_verse,
            "ai_verse": None,
            "winner": "user",
            "game_token": _encode_game_token(payload),
            "reply": generate_poetry_reply(
                persona=persona,
                user=user,
                verses=verses,
                history=history,
                message=message,
                event="ai_lost",
                target=target,
            ),
        }

    verses.append({"verse": ai_verse, "player": "ai"})
    payload["verses"] = verses
    return {
        "accepted": True,
        "user_verse": user_verse,
        "ai_verse": ai_verse,
        "winner": None,
        "game_token": _encode_game_token(payload),
        "reply": generate_poetry_reply(
            persona=persona,
            user=user,
            verses=verses,
            history=history,
            message=message,
            event="valid",
            target=target,
            ai_verse=ai_verse,
            user_verse=user_verse,
            add_commentary=random.SystemRandom().random() < ROUND_COMMENTARY_PROBABILITY,
        ),
    }
