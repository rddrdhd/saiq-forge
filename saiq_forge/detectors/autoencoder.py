import torch
import torch.nn as nn

from saiq_forge.detectors.base import Detector
from saiq_forge.detectors.registry import register


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


class _DenseAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dims, latent_dim):
        super().__init__()

        encoder_layers = []
        in_features = input_dim
        for h_dim in hidden_dims:
            encoder_layers += [nn.Linear(in_features, h_dim), nn.ReLU()]
            in_features = h_dim
        encoder_layers.append(nn.Linear(in_features, latent_dim))
        self.encoder = nn.Sequential(*encoder_layers)

        decoder_layers = []
        in_features = latent_dim
        for h_dim in reversed(hidden_dims):
            decoder_layers += [nn.Linear(in_features, h_dim), nn.ReLU()]
            in_features = h_dim
        decoder_layers.append(nn.Linear(in_features, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

    def forward(self, x):
        return self.decoder(self.encoder(x))


@register("deep_learning", "autoencoder_classical")
class ClassicalAutoencoderDetector(Detector):
    """Standard dense-autoencoder anomaly detector: trained exclusively on
    normal traffic, scored by reconstruction error against a mean+3-sigma
    threshold from the training set (danger branch's
    core/modules/engine.py::run_inference_and_flag convention, ported here
    single-process — no torch.distributed, since that machinery exists for
    real-time HPC throughput benchmarking, not this comparison)."""

    tier = "gpu_deep_learning"

    def __init__(
        self,
        hidden_dims=(8,),
        latent_dim=2,
        epochs=50,
        batch_size=32,
        learning_rate=1e-3,
        seed=0,
        **_ignored,
    ):
        self.hidden_dims = list(hidden_dims)
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.seed = seed
        self._model = None
        self._feature_keys = None
        self._threshold = None

    def fit(self, feature_vectors):
        if not feature_vectors:
            raise ValueError("cannot fit on zero feature vectors")
        torch.manual_seed(self.seed)

        self._feature_keys = sorted(feature_vectors[0])
        x = self._to_tensor(feature_vectors)

        self._model = _DenseAutoencoder(x.shape[1], self.hidden_dims, self.latent_dim)
        optimizer = torch.optim.Adam(self._model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss(reduction="none")

        self._model.train()
        n = x.shape[0]
        for _ in range(self.epochs):
            perm = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                batch = x[perm[start:start + self.batch_size]]
                optimizer.zero_grad()
                loss = criterion(self._model(batch), batch).mean()
                loss.backward()
                optimizer.step()

        self._model.eval()
        with torch.no_grad():
            errors = criterion(self._model(x), x).mean(dim=1)
        mean = errors.mean().item()
        std = errors.std(unbiased=False).item()
        threshold = mean + 3 * std
        self._threshold = threshold if threshold > 0 else 1.0

    def score(self, feature_vectors):
        if self._model is None:
            raise RuntimeError("fit() must be called before score()")
        x = self._to_tensor(feature_vectors)
        self._model.eval()
        with torch.no_grad():
            errors = nn.functional.mse_loss(self._model(x), x, reduction="none").mean(dim=1)
        return [_clip01(error.item() / self._threshold) for error in errors]

    def _to_tensor(self, feature_vectors):
        return torch.tensor(
            [[fv[key] for key in self._feature_keys] for fv in feature_vectors],
            dtype=torch.float32,
        )
