import torch  # type: ignore[import-not-found]
import torch.nn as nn  # type: ignore[import-not-found]

class ResidualBlock(nn.Module):
    def __init__(self, in_features):
        super(ResidualBlock, self).__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_features, in_features, 3, 1, 1, bias=False),
            nn.InstanceNorm2d(in_features),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_features, in_features, 3, 1, 1, bias=False),
            nn.InstanceNorm2d(in_features)
        )

    def forward(self, x):
        return x + self.block(x)

class DummyVTONGenerator(nn.Module):
    """
    Đây là khung sườn (Skeleton architecture) giả lập mạn U-Net Generator của VITON.
    Nhóm bạn nên copy mã nguồn kiến trúc gốc của CP-VTON (File networks.py của họ) 
    và thay thế các class GMM / TOM vào package này.
    
    Cấu trúc đầu vào cơ bản: 
    - Ảnh Person map (shape: C_in, H, W)
    - Ảnh Cloth c_map (shape: 3, H, W)
    """
    def __init__(self, input_nc=6, output_nc=3, n_residual_blocks=3):
        super(DummyVTONGenerator, self).__init__()

        # Initial convolution block       
        model = [   
            nn.Conv2d(input_nc, 64, 7, 1, 3, padding_mode='reflect'),
            nn.InstanceNorm2d(64),
            nn.ReLU(inplace=True) 
        ]

        # Downsampling
        in_features = 64
        out_features = in_features * 2
        for _ in range(2):
            model += [  
                nn.Conv2d(in_features, out_features, 3, 2, 1),
                nn.InstanceNorm2d(out_features),
                nn.ReLU(inplace=True) 
            ]
            in_features = out_features
            out_features = in_features * 2

        # Residual blocks
        for _ in range(n_residual_blocks):
            model += [ResidualBlock(in_features)]

        # Upsampling
        out_features = in_features // 2
        for _ in range(2):
            model += [  
                nn.ConvTranspose2d(in_features, out_features, 3, 2, 1, output_padding=1),
                nn.InstanceNorm2d(out_features),
                nn.ReLU(inplace=True) 
            ]
            in_features = out_features
            out_features = in_features // 2

        # Output layer
        model += [  
            nn.Conv2d(64, output_nc, 7, 1, 3, padding_mode='reflect'),
            nn.Tanh() 
        ]

        self.model = nn.Sequential(*model)

    def forward(self, person_map, cloth_map):
        # Concatenate person and cloth map along channels
        x = torch.cat([person_map, cloth_map], dim=1)
        return self.model(x)

class DummyDiscriminator(nn.Module):
    def __init__(self, input_nc=3):
        super(DummyDiscriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(input_nc, 64, 4, 2, 1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(64, 128, 4, 2, 1),
            nn.InstanceNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(128, 1, 4, 1, 1)
        )

    def forward(self, x):
        return self.model(x)
