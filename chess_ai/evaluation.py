from __future__ import annotations

from typing import TYPE_CHECKING

import chess
import numpy as np

from chess_ai.board_encoding import encode_board

if TYPE_CHECKING:
    from chess_ai.model import ChessValueNet


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

PIECE_SQUARE_TABLES = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ],
    chess.ROOK: [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    ],
    chess.KING: [
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
    ],
}


def material_score(board: chess.Board) -> float:
    score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value
    return score / 3900.0


def positional_score(board: chess.Board) -> float:
    score = 0
    for square, piece in board.piece_map().items():
        table = PIECE_SQUARE_TABLES[piece.piece_type]
        index = square if piece.color == chess.WHITE else chess.square_mirror(square)
        value = table[index]
        score += value if piece.color == chess.WHITE else -value
    return score / 1200.0


def mobility_score(board: chess.Board) -> float:
    turn = board.turn
    board.turn = chess.WHITE
    white_moves = board.legal_moves.count()
    board.turn = chess.BLACK
    black_moves = board.legal_moves.count()
    board.turn = turn
    return (white_moves - black_moves) / 120.0


def king_safety_score(board: chess.Board) -> float:
    score = 0.0
    if board.is_check():
        score += -0.08 if board.turn == chess.WHITE else 0.08
    if board.has_kingside_castling_rights(chess.WHITE) or board.has_queenside_castling_rights(chess.WHITE):
        score += 0.03
    if board.has_kingside_castling_rights(chess.BLACK) or board.has_queenside_castling_rights(chess.BLACK):
        score -= 0.03
    return score


def classical_score(board: chess.Board) -> float:
    value = (
        0.72 * material_score(board)
        + 0.18 * positional_score(board)
        + 0.07 * mobility_score(board)
        + king_safety_score(board)
    )
    return max(min(value, 0.98), -0.98)


def terminal_score(board: chess.Board) -> float | None:
    if board.is_checkmate():
        return -1.0 if board.turn == chess.WHITE else 1.0
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0.0
    return None


class Evaluator:
    """Combines a neural value network with a stable material baseline."""

    def __init__(
        self,
        model: ChessValueNet | None = None,
        device: str = "cpu",
        neural_weight: float = 0.55,
    ) -> None:
        self.model = model
        self.device = device
        self.neural_weight = neural_weight

    def evaluate(self, board: chess.Board) -> float:
        terminal = terminal_score(board)
        if terminal is not None:
            return terminal

        classical = classical_score(board)
        if self.model is None:
            return classical

        import torch

        encoded = encode_board(board)
        x = torch.tensor(np.expand_dims(encoded, axis=0), dtype=torch.float32, device=self.device)
        with torch.no_grad():
            neural = float(self.model(x).item())
        return (self.neural_weight * neural) + ((1.0 - self.neural_weight) * classical)
