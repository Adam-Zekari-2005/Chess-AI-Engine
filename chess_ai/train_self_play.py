from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

from chess_ai.engine import ChessEngine, Level
from chess_ai.evaluation import Evaluator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate self-play games for value training.")
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--max-plies", type=int, default=160)
    parser.add_argument("--output", default="data/self_play.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    evaluator = Evaluator(model=None)
    engine = ChessEngine(evaluator=evaluator, level=Level.MEDIUM, seed=42)

    with output.open("w", encoding="utf-8") as handle:
        for game_index in range(args.games):
            board = chess.Board()
            positions: list[str] = []
            while not board.is_game_over(claim_draw=True) and len(positions) < args.max_plies:
                positions.append(board.fen())
                move = engine.choose_move(board).move
                board.push(move)

            result = board.result(claim_draw=True)
            for fen in positions:
                handle.write(json.dumps({"fen": fen, "result": result}) + "\n")
            print(f"game={game_index + 1}/{args.games} result={result} positions={len(positions)}")

    print(f"Saved dataset to {output}")


if __name__ == "__main__":
    main()
