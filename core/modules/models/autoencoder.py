import torch
import torch.nn as nn

class NetworkAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(NetworkAutoencoder, self).__init__()
        
        # Compress the data
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4) # Latent bottleneck
        )
        
        # Reconstruct the data
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded