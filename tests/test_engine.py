import chess

from chess_ai.engine import ChessEngine, Level
from chess_ai.evaluation import Evaluator


def test_engine_returns_legal_move():
    board = chess.Board()
    engine = ChessEngine(Evaluator(model=None), level=Level.EASY, seed=1)
    result = engine.choose_move(board)
    assert result.move in board.legal_moves
