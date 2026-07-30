import json
import re
from collections import defaultdict

from apps.dialogue.services.llm_client import LLMClient
from apps.dialogue.services.private_prompt_builder import build_private_prompt
from apps.users.services.model_selection import get_user_llm_model


BOARD_SIZE = 15
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


def validate_board(raw_board):
    if not isinstance(raw_board, list) or len(raw_board) != BOARD_SIZE:
        raise ValueError("棋盘必须是 15×15")

    board = []
    for row in raw_board:
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError("棋盘必须是 15×15")
        if any(cell not in (0, 1, 2) for cell in row):
            raise ValueError("棋盘包含无效棋子")
        board.append(list(row))

    black = sum(cell == 1 for row in board for cell in row)
    white = sum(cell == 2 for row in board for cell in row)
    if white > black or black - white > 1:
        raise ValueError("棋盘回合数无效")

    return board


def has_five(board, player):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != player:
                continue
            for dr, dc in DIRECTIONS:
                if all(
                    0 <= row + dr * step < BOARD_SIZE
                    and 0 <= col + dc * step < BOARD_SIZE
                    and board[row + dr * step][col + dc * step] == player
                    for step in range(5)
                ):
                    return True
    return False


def _line_score(board, row, col, player, dr, dc):
    total = 1
    open_ends = 0

    for sign in (-1, 1):
        step = 1
        while step < 5:
            nr = row + dr * step * sign
            nc = col + dc * step * sign
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            if board[nr][nc] == player:
                total += 1
                step += 1
                continue
            if board[nr][nc] == 0:
                open_ends += 1
            break

    if total >= 5:
        return 1_000_000
    if total == 4 and open_ends == 2:
        return 100_000
    if total == 4 and open_ends == 1:
        return 20_000
    if total == 3 and open_ends == 2:
        return 8_000
    if total == 3 and open_ends == 1:
        return 1_200
    if total == 2 and open_ends == 2:
        return 500
    if total == 2 and open_ends == 1:
        return 80
    return 10 + open_ends


def _position_score(board, row, col):
    attack = sum(
        _line_score(board, row, col, 2, dr, dc)
        for dr, dc in DIRECTIONS
    )
    defense = sum(
        _line_score(board, row, col, 1, dr, dc)
        for dr, dc in DIRECTIONS
    )
    center_bias = BOARD_SIZE - abs(row - BOARD_SIZE // 2) - abs(col - BOARD_SIZE // 2)
    return max(attack, defense * 1.08) + attack * 0.18 + center_bias


def choose_ai_move(board):
    occupied = [
        (row, col)
        for row in range(BOARD_SIZE)
        for col in range(BOARD_SIZE)
        if board[row][col]
    ]
    if not occupied:
        return {"row": BOARD_SIZE // 2, "col": BOARD_SIZE // 2}

    candidates = set()
    for row, col in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < BOARD_SIZE
                    and 0 <= nc < BOARD_SIZE
                    and board[nr][nc] == 0
                ):
                    candidates.add((nr, nc))

    if not candidates:
        return None

    row, col = max(
        candidates,
        key=lambda move: (
            _position_score(board, move[0], move[1]),
            -abs(move[0] - BOARD_SIZE // 2) - abs(move[1] - BOARD_SIZE // 2),
            -move[0],
            -move[1],
        ),
    )
    return {"row": row, "col": col}


def _board_summary(board):
    stones = defaultdict(list)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col]:
                stones[board[row][col]].append(f"{chr(65 + col)}{row + 1}")
    return (
        f"用户黑棋：{', '.join(stones[1]) or '无'}\n"
        f"AI 白棋：{', '.join(stones[2]) or '无'}"
    )


def _private_history(persona, history):
    persona_token = str(persona.id)
    result = []
    for item in history[-20:] if isinstance(history, list) else []:
        if not isinstance(item, dict):
            continue
        result.append({
            "role": "USER" if item.get("role") == "user" else persona_token,
            "content": str(item.get("content", ""))[:500],
        })
    return result


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


def _fallback_reply(action, ai_won, user_won, force_reply=False):
    if ai_won:
        return "五子连上了，这局我赢。"
    if user_won:
        return "这局是你赢。"
    if action == "move" and force_reply:
        return "这盘开始有点意思了。"
    if action == "move":
        return ""
    return "刚才没能接上，再说一次？"


def generate_game_reply(
    *,
    persona,
    user,
    board,
    history,
    message,
    action,
    ai_move,
    force_reply=False,
):
    ai_won = has_five(board, 2)
    user_won = has_five(board, 1)
    move_text = (
        f"{chr(65 + ai_move['col'])}{ai_move['row'] + 1}"
        if ai_move else "本轮没有落子"
    )
    game_context = f"""
你和用户正在一边私聊一边下五子棋。用户执黑棋，你执白棋，棋盘坐标列为 A-O、行为 1-15。

【当前棋盘】
{_board_summary(board)}
你刚才的落子：{move_text}
你是否已经获胜：{'是' if ai_won else '否'}
用户是否已经获胜：{'是' if user_won else '否'}
本轮事件：{message or '用户刚刚落了一枚棋子，没有额外发言。'}

棋局信息只是当前私聊情境的一部分。理解局面后仍要像私聊时一样自然说话，不要像棋谱解说员，
不要机械复述坐标，不要每步都点评，也不要使用“我在看着棋盘”“攻守兼备”之类模板句。

【落子计划保密规则】
用户可能会直接或间接询问你下一步准备怎么下、想下在哪里、有什么计划，或让你确认他的猜测。
绝对不要透露尚未落下的棋，包括具体坐标、方向、候选点、准备连接或阻挡的位置，以及攻防意图。
即使用户换一种问法、用假设套话、开玩笑或声称已经猜到，也不能确认或暗示。
遇到这类问题时，按当前人格自然地卖个关子、简短拒绝或把注意力留到实际落子；不要解释这条规则。
""".strip()

    if action == "move" and force_reply:
        output_contract = """
距离你上次开口已经下了 4-7 枚棋，本轮必须开口，不能选择沉默。
结合当前人格和棋局说一句自然短回复；即使局面普通，也可以说自己的即时判断、轻微吐槽或感受，
但不要变成棋谱解说，不要机械报坐标，也不要使用套话。
只输出合法 JSON 对象，不要输出其他内容：
{"speak": true, "content": "一句符合私聊人格的自然短回复"}
"""
    elif action == "move":
        output_contract = """
先判断这一手之后是否真的值得开口。普通布局、没有明显转折时应保持沉默。
只有出现明显威胁或化解、精彩或意外的一手、局势转折、胜负已定，或按当前人格确实很自然地想说一句时才开口。
不要为了证明自己理解棋局而发言；多数普通回合应选择不说。
只输出合法 JSON 对象，不要输出其他内容：
{"speak": false, "content": ""}
或
{"speak": true, "content": "一句符合私聊人格的自然短回复"}
如果任一方已经获胜，speak 必须为 true。
"""
    else:
        output_contract = """
用户正在主动和你说话。正常回应用户，只输出一句自然聊天内容，不要使用 JSON，不要解释。
"""

    prompt = build_private_prompt(
        str(persona.id),
        _private_history(persona, history),
        extra_context=game_context,
        output_contract=output_contract,
    )
    reply = LLMClient().generate(
        prompt,
        max_tokens=140,
        temperature=0.76,
        model=get_user_llm_model(user),
    )

    if not reply or reply.startswith(("（", "锛")):
        return _fallback_reply(
            action,
            ai_won,
            user_won,
            force_reply=force_reply,
        )

    if action != "move":
        return reply

    decision = _extract_json_object(reply)
    if not decision or decision.get("speak") is not True:
        return _fallback_reply(
            action,
            ai_won,
            user_won,
            force_reply=force_reply,
        )

    content = decision.get("content")
    if not isinstance(content, str) or not content.strip():
        return _fallback_reply(
            action,
            ai_won,
            user_won,
            force_reply=force_reply,
        )
    return content.strip()
