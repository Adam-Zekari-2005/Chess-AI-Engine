from __future__ import annotations

import argparse
from pathlib import Path

import chess

from chess_ai.engine import ChessEngine, Level
from chess_ai.evaluation import Evaluator
from chess_ai.model import load_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play chess against a PyTorch-powered AI.")
    parser.add_argument("--level", choices=[level.value for level in Level], default="medium")
    parser.add_argument("--human", choices=["white", "black"], default="white")
    parser.add_argument("--backend", choices=["pytorch", "tensorflow"], default="pytorch")
    parser.add_argument("--model", default=None, help="Optional path to a trained model.")
    return parser.parse_args()


def load_evaluator(model_path: str | None, backend: str) -> Evaluator:
    if model_path is None:
        print("No model provided: using material evaluation + minimax.")
        return Evaluator(model=None)
    if not Path(model_path).exists():
        print(f"Model not found: {model_path}")
        print("Using material evaluation + minimax instead.")
        return Evaluator(model=None)
    if backend == "tensorflow":
        from chess_ai.tf_evaluation import TensorFlowEvaluator
        from chess_ai.tf_model import load_tf_model

        print(f"Loaded TensorFlow model: {model_path}")
        return TensorFlowEvaluator(model=load_tf_model(model_path))  # type: ignore[return-value]
    model = load_model(model_path)
    print(f"Loaded PyTorch model: {model_path}")
    return Evaluator(model=model)


def print_board(board: chess.Board) -> None:
    print()
    print(board.unicode(borders=True, empty_square="."))
    print(f"FEN: {board.fen()}")
    print()


def ask_move(board: chess.Board) -> chess.Move:
    while True:
        raw = input("Your move (UCI, example e2e4): ").strip()
        try:
            move = chess.Move.from_uci(raw)
        except ValueError:
            print("Invalid format. Try e2e4, g1f3 or e7e8q.")
            continue
        if move in board.legal_moves:
            return move
        print("Illegal move in this position.")


def main() -> None:
    args = parse_args()
    board = chess.Board()
    human_color = chess.WHITE if args.human == "white" else chess.BLACK
    evaluator = load_evaluator(args.model, args.backend)
    engine = ChessEngine(evaluator=evaluator, level=Level(args.level))

    print("PyTorch Chess AI")
    print(f"Level: {args.level} | You play: {args.human}")

    while not board.is_game_over(claim_draw=True):
        print_board(board)
        if board.turn == human_color:
            board.push(ask_move(board))
        else:
            print("AI is thinking...")
            result = engine.choose_move(board)
            board.push(result.move)
            print(f"AI plays {result.move.uci()} | score={result.score:.3f} | nodes={result.nodes}")

    print_board(board)
    print(f"Game over: {board.result(claim_draw=True)}")
    print(board.outcome(claim_draw=True))


if __name__ == "__main__":
    main()
