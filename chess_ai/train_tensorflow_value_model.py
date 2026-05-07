from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
import numpy as np
import tensorflow as tf

from chess_ai.board_encoding import encode_board, result_to_value
from chess_ai.tf_model import build_tf_chess_value_net


def load_dataset(path: str) -> tuple[np.ndarray, np.ndarray]:
    boards: list[np.ndarray] = []
    values: list[float] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            board = chess.Board(item["fen"])
            boards.append(encode_board(board))
            values.append(result_to_value(item["result"]))
    return np.asarray(boards, dtype=np.float32), np.asarray(values, dtype=np.float32)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the TensorFlow chess value network.")
    parser.add_argument("--data", default="data/self_play.jsonl")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output", default="models/tf_chess_value_net.keras")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    x, y = load_dataset(args.data)
    model = build_tf_chess_value_net()
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=args.lr, weight_decay=1e-4),
        loss="mse",
        metrics=[tf.keras.metrics.MeanAbsoluteError(name="mae")],
    )
    model.fit(x, y, epochs=args.epochs, batch_size=args.batch_size, validation_split=0.1)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save(output)
    print(f"Saved TensorFlow model to {output}")


if __name__ == "__main__":
    main()
