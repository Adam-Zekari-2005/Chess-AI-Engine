from __future__ import annotations

import chess
import numpy as np


PIECE_TO_PLANE = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
    chess.KING: 5,
}


def encode_board(board: chess.Board) -> np.ndarray:
    """Encode a board as a 18x8x8 tensor.

    Planes 0..5 contain white pieces, planes 6..11 black pieces.
    Planes 12..17 contain global state repeated over the board.
    """
    tensor = np.zeros((18, 8, 8), dtype=np.float32)

    for square, piece in board.piece_map().items():
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        offset = 0 if piece.color == chess.WHITE else 6
        tensor[offset + PIECE_TO_PLANE[piece.piece_type], row, col] = 1.0

    tensor[12, :, :] = 1.0 if board.turn == chess.WHITE else 0.0
    tensor[13, :, :] = 1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0
    tensor[14, :, :] = 1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0
    tensor[15, :, :] = 1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0
    tensor[16, :, :] = 1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0
    tensor[17, :, :] = min(board.fullmove_number / 100.0, 1.0)
    return tensor


def result_to_value(result: str) -> float:
    """Convert a chess result to a value from White's perspective."""
    if result == "1-0":
        return 1.0
    if result == "0-1":
        return -1.0
    return 0.0
