from __future__ import annotations

import tensorflow as tf


def build_tf_chess_value_net() -> tf.keras.Model:
    """TensorFlow/Keras version of the chess value network."""
    inputs = tf.keras.Input(shape=(18, 8, 8), name="board")
    x = tf.keras.layers.Permute((2, 3, 1))(inputs)
    x = tf.keras.layers.Conv2D(64, kernel_size=3, padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(96, kernel_size=3, padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(96, kernel_size=3, padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.15)(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    outputs = tf.keras.layers.Dense(1, activation="tanh", name="value")(x)
    return tf.keras.Model(inputs=inputs, outputs=outputs, name="tf_chess_value_net")


def load_tf_model(path: str) -> tf.keras.Model:
    return tf.keras.models.load_model(path)
