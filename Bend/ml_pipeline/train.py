import os
import argparse
import torch  # type: ignore[import-not-found]
import torch.nn as nn  # type: ignore[import-not-found]
from torch.utils.data import DataLoader  # type: ignore[import-not-found]
from Bend.ml_pipeline.dataset import VTONDataset
from Bend.ml_pipeline.models.gan_architecture import DummyVTONGenerator, DummyDiscriminator


def train():
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình GAN VITON/CP-VTON")
    parser.add_argument("--data_root", type=str, default="../data", help="Đường dẫn thư mục chứa dataset chuẩn (images, clothes...)")
    parser.add_argument("--image_height", type=int, default=256)
    parser.add_argument("--image_width", type=int, default=192)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=0.0002)
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    print(f"🚀 Bắt đầu quá trình huấn luyện trên: {args.device}")

    # 1. Khởi tạo mô hình
    generator = DummyVTONGenerator(input_nc=6, output_nc=3).to(args.device)
    discriminator = DummyDiscriminator(input_nc=3).to(args.device)

    # 2. Khởi tạo Dataset
    dataset = VTONDataset(data_root=args.data_root, mode='train', image_size=(args.image_height, args.image_width))
    if len(dataset) == 0:
        print("Dataset trống. Tạm dừng tiến trình. Vui lòng kiểm tra lại pairs.txt!")
        return
        
    # Giới hạn num_workers trên Laptop cá nhân tránh CPU quá tải
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)

    # 3. Định nghĩa tiêu chuẩn Mất mát (Loss) và Tối ưu (Optimizer)
    criterion_gan = nn.MSELoss() # LSGAN loss
    criterion_pixel = nn.L1Loss() # Pixel-wise L1 Loss

    optimizer_G = torch.optim.Adam(generator.parameters(), lr=args.lr, betas=(0.5, 0.999))
    optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=args.lr, betas=(0.5, 0.999))

    # Tủ đồ lưu trữ checkpoint trọng số
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    # 4. Vòng lặp huấn luyện chính
    for epoch in range(args.epochs):
        for i, batch in enumerate(dataloader):
            # Tuỳ kiến trúc VITON mà batching ở đây sẽ cấp: Agnostic person (Ảnh người che áo), Target Cloth, và Pose
            img_real = batch['image'].to(args.device)
            cloth = batch['cloth'].to(args.device)

            # --- A. Huấn luyện Discriminator ---
            optimizer_D.zero_grad()
            
            # Generator sinh ảnh giả
            img_fake = generator(img_real, cloth) 
            
            # Loss mẫu THẬT và GIẢ
            pred_real = discriminator(img_real)
            loss_D_real = criterion_gan(pred_real, torch.ones_like(pred_real))
            
            pred_fake = discriminator(img_fake.detach())
            loss_D_fake = criterion_gan(pred_fake, torch.zeros_like(pred_fake))
            
            loss_D = (loss_D_real + loss_D_fake) * 0.5
            loss_D.backward()
            optimizer_D.step()

            # --- B. Huấn luyện Generator ---
            optimizer_G.zero_grad()
            
            # G đánh lừa D
            pred_fake = discriminator(img_fake)
            loss_G_gan = criterion_gan(pred_fake, torch.ones_like(pred_fake))
            
            # Pixel loss đo lường độ chân thực so với ảnh gốc
            loss_G_pixel = criterion_pixel(img_fake, img_real) * 10.0 
            
            loss_G = loss_G_gan + loss_G_pixel
            loss_G.backward()
            optimizer_G.step()

            if i % 10 == 0:
                print(f"[Epoch {epoch}/{args.epochs}] [Batch {i}/{len(dataloader)}] [D loss: {loss_D.item():.4f}] [G loss: {loss_G.item():.4f}]")

        # Lưu Checkpoint mỗi epoch
            checkpoint_path = os.path.join(args.checkpoint_dir, f"vton_gen_epoch_{epoch}.pth")
            torch.save(generator.state_dict(), checkpoint_path)
        print(f"✅ Đã lưu Checkpoint Weights cho epoch {epoch}")

if __name__ == "__main__":
    train()
