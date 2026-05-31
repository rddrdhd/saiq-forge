import torch
import torch.nn as nn

class NetworkAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dims, latent_dim):
        super(NetworkAutoencoder, self).__init__()
        
        # --- 1. Build Dynamic Encoder ---
        encoder_layers = []
        in_features = input_dim
        
        # Iterate through the config list (e.g., [32, 16])
        for h_dim in hidden_dims:
            encoder_layers.append(nn.Linear(in_features, h_dim))
            encoder_layers.append(nn.ReLU())
            in_features = h_dim  # The output of this layer is the input to the next
            
        # Add the final bottleneck layer
        encoder_layers.append(nn.Linear(in_features, latent_dim))
        self.encoder = nn.Sequential(*encoder_layers)
        
        # --- 2. Build Dynamic Decoder ---
        decoder_layers = []
        # Reverse the hidden layers for the decoder (e.g., [16, 32])
        decoder_hidden_dims = hidden_dims[::-1] 
        in_features = latent_dim
        
        for h_dim in decoder_hidden_dims:
            decoder_layers.append(nn.Linear(in_features, h_dim))
            decoder_layers.append(nn.ReLU())
            in_features = h_dim
            
        # Final output layer must match the original input dimension
        decoder_layers.append(nn.Linear(in_features, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded