from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from chess_ai.board_encoding import encode_board, result_to_value
from chess_ai.model import ChessValueNet


class ChessPositionDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, path: str) -> None:
        self.rows: list[tuple[str, float]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                self.rows.append((item["fen"], result_to_value(item["result"])))

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        fen, value = self.rows[index]
        board = chess.Board(fen)
        x = torch.tensor(encode_board(board), dtype=torch.float32)
        y = torch.tensor(value, dtype=torch.float32)
        return x, y


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the PyTorch chess value network.")
    parser.add_argument("--data", default="data/self_play.jsonl")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output", default="models/chess_value_net.pt")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dataset = ChessPositionDataset(args.data)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    model = ChessValueNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    for epoch in range(1, args.epochs + 1):
        losses: list[float] = []
        model.train()
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            prediction = model(x)
            loss = loss_fn(prediction, y)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))

        print(f"epoch={epoch} loss={np.mean(losses):.4f}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output)
    print(f"Saved model to {output}")


if __name__ == "__main__":
    main()
