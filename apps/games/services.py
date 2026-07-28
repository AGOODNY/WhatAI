from collections import defaultdict

from apps.dialogue.services.llm_client import LLMClient
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


def _fallback_reply(persona, action, ai_move, ai_won):
    name = persona.name
    if ai_won:
        return f"五子连珠。承让啦，这一局是我赢了。要不要和{name}再来一盘？"
    if action == "move" and ai_move:
        coordinate = f"{chr(65 + ai_move['col'])}{ai_move['row'] + 1}"
        return f"我落在 {coordinate}。这一步我既要顾着自己的连线，也得提防你的攻势。"
    return "我一直看着棋盘呢。你可以聊聊你的思路，也可以继续落子。"


def generate_game_reply(*, persona, user, board, history, message, action, ai_move):
    ai_won = has_five(board, 2)
    user_won = has_five(board, 1)
    recent_history = history[-10:] if isinstance(history, list) else []
    history_text = "\n".join(
        f"{'用户' if item.get('role') == 'user' else persona.name}："
        f"{str(item.get('content', ''))[:300]}"
        for item in recent_history
        if isinstance(item, dict)
    ) or "暂无聊天"
    move_text = (
        f"{chr(65 + ai_move['col'])}{ai_move['row'] + 1}"
        if ai_move else "本轮没有落子"
    )

    prompt = f"""
你正在以“{persona.name}”的身份和用户一边聊天一边下五子棋。

【人格设定】
简介：{persona.description or '自然、友好'}
说话风格：{persona.speaking_style or '自然口语'}
补充设定：{persona.personality_prompt or '无'}

【规则与当前状态】
用户执黑棋（1），你执白棋（2），棋盘坐标列为 A-O、行为 1-15。
{_board_summary(board)}
你刚才的落子：{move_text}
你是否已经获胜：{'是' if ai_won else '否'}
用户是否已经获胜：{'是' if user_won else '否'}

【最近聊天】
{history_text}

【用户最新内容】
{message or '用户刚刚落了一枚棋子，没有额外发言。'}

请用符合人格的中文回复 1-3 句。你必须理解并可以评论当前棋局，但不要虚构棋盘上没有的棋子，
不要输出程序格式、坐标指令或下一步落子；落子已经由规则引擎完成。聊天要自然，可以回应用户，
也可以简短点评刚才的攻防。如果你已获胜，可以自然地庆祝；如果用户获胜，应大方承认结果。
不要声称自己获胜，除非上面明确为“是”。
""".strip()

    reply = LLMClient().generate(
        prompt,
        max_tokens=160,
        temperature=0.75,
        model=get_user_llm_model(user),
    )
    if not reply or reply.startswith(("（", "锛")):
        if user_won:
            return f"这一手漂亮，确实已经连成五子了。是你赢了，{persona.name}认输！"
        return _fallback_reply(persona, action, ai_move, ai_won)
    return reply
