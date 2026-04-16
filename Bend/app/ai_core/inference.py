import os
import torch
import torchvision.transforms as transforms
from PIL import Image

import sys
# Tạm thời hack sys path để tái sử dụng module architecture trong thư mục ml_pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ml_pipeline')))
from models.gan_architecture import DummyVTONGenerator

class VTONInference:
    """
    Singleton Class quản lý cấu trúc nạp Model VTON vào PyTorch.
    Đảm bảo Model weights chỉ tốn thời gian Load 1 lần duy nhất khi Server start lên.
    Tránh trường hợp mỗi request lại Instantiate thêm 1 Model gây Out of Memory (OOM).
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VTONInference, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def initialize(self, weight_path=None, device=None):
        if self.initialized:
            return
            
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔥 Đang nạp Model (VITON/CP-VTON) vào hệ thống: {self.device}...")
        
        # Khởi tạo mạng Generator
        self.model = DummyVTONGenerator(input_nc=6, output_nc=3).to(self.device)
        self.model.eval() # Bắt buộc phải Eval để Freeze Batch Norm và Dropout
        
        if weight_path and os.path.exists(weight_path):
            try:
                self.model.load_state_dict(torch.load(weight_path, map_location=self.device))
                print(f"✅ Đã nạp thành công Weight: {weight_path}")
            except Exception as e:
                print(f"❌ Lỗi nạp Model Weights: {e}")
        else:
            print("⚠️ CẢNH BÁO: Đang chạy Inference ngẫu nhiên (Dummy Blank Model) vì chưa có thư mục Weights!")
        
        self.transform = transforms.Compose([
            transforms.Resize((512, 512)), # Resize chuẩn đồ án
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        
        self.initialized = True
        
    def infer(self, person_image_path: str, cloth_image_path: str) -> Image.Image:
        """
        Nhận vào đường dẫn file ảnh Person và file Cloth
        Chạy qua GAN để sinh ra ảnh (Texture) output mới.
        """
        if not self.initialized:
            self.initialize()
            
        try:
            person_img = Image.open(person_image_path).convert('RGB')
            cloth_img = Image.open(cloth_image_path).convert('RGB')
            
            # Tiền xử lý (Thêm chiều Batch size = 1)
            p_tensor = self.transform(person_img).unsqueeze(0).to(self.device)
            c_tensor = self.transform(cloth_img).unsqueeze(0).to(self.device)
            
            with torch.no_grad(): # CHỐNG TRÀN VRAM - Bắt buộc khi Inference
                output_tensor = self.model(p_tensor, c_tensor)
                
            # Đưa Tensor chuẩn GAN (-1 đến 1) về lại dạng Image màu (0 đến 1)
            output_tensor = (output_tensor.squeeze(0).cpu() * 0.5) + 0.5 
            output_tensor = torch.clamp(output_tensor, 0, 1)
            
            transform_to_pil = transforms.ToPILImage()
            return transform_to_pil(output_tensor)
            
        except Exception as e:
            print(f"❌ VTON Inference Crash: {e}")
            raise e
