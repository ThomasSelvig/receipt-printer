from io import BytesIO
import re
import textwrap
from typing import Optional, Tuple
import qrcode
import markdown
from PIL import Image, ImageDraw, ImageFont


class ImageBackend:
    def __init__(self, max_width: int = 512, font_size: int = 16, line_spacing: int = 4):
        self.max_width = max_width
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.padding = 20
        
        try:
            self.font = ImageFont.load_default()
        except Exception:
            self.font = ImageFont.load_default()
    
    def _estimate_text_size(self, text: str) -> Tuple[int, int]:
        lines = text.split('\n')
        max_line_width = 0
        total_height = 0
        
        for line in lines:
            bbox = self.font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            max_line_width = max(max_line_width, line_width)
            total_height += line_height + self.line_spacing
        
        return max_line_width, total_height
    
    def _wrap_text(self, text: str, max_chars_per_line: int = 60) -> str:
        lines = text.split('\n')
        wrapped_lines = []
        
        for line in lines:
            if not line.strip():
                wrapped_lines.append('')
                continue
            
            wrapped = textwrap.fill(line, width=max_chars_per_line, 
                                  break_long_words=False, 
                                  break_on_hyphens=False)
            wrapped_lines.append(wrapped)
        
        return '\n'.join(wrapped_lines)
    
    def _render_markdown_to_text(self, markdown_text: str) -> str:
        html = markdown.markdown(markdown_text)
        
        # Simple HTML to text conversion for receipt printing
        # Remove HTML tags and convert to plain text with formatting hints
        text = html
        
        # Convert headers
        text = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'=== \1 ===', text)
        
        # Convert bold
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
        
        # Convert italic
        text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
        text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
        
        # Convert code
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
        
        # Convert lists
        text = re.sub(r'<li>(.*?)</li>', r'• \1', text)
        text = re.sub(r'<ul>(.*?)</ul>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<ol>(.*?)</ol>', r'\1', text, flags=re.DOTALL)
        
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def text_to_image(self, text: str, is_markdown: bool = False) -> Image.Image:
        if is_markdown:
            text = self._render_markdown_to_text(text)
        
        # Wrap text to fit receipt width
        wrapped_text = self._wrap_text(text)
        
        # Estimate image size needed
        text_width, text_height = self._estimate_text_size(wrapped_text)
        
        # Create image with padding
        img_width = min(self.max_width, text_width + self.padding * 2)
        img_height = text_height + self.padding * 2
        
        # Create white background image
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw text
        y_offset = self.padding
        for line in wrapped_text.split('\n'):
            if line.strip():
                # Handle basic formatting indicators
                font_to_use = self.font
                text_to_draw = line
                
                # Simple bold handling (for **text**)
                if '**' in line:
                    text_to_draw = line.replace('**', '')
                
                # Simple italic handling (for *text*)
                if '*' in line and '**' not in line:
                    text_to_draw = line.replace('*', '')
                
                # Handle headers (=== text ===)
                if line.startswith('===') and line.endswith('==='):
                    text_to_draw = line.replace('=', '').strip()
                
                draw.text((self.padding, y_offset), text_to_draw, 
                         fill='black', font=font_to_use)
            
            bbox = self.font.getbbox('A')  # Use a reference character
            line_height = bbox[3] - bbox[1]
            y_offset += line_height + self.line_spacing
        
        return image
    
    def generate_qr_code(self, data: str) -> Image.Image:
        # Calculate optimal QR code size for max_width
        # QR codes have a minimum size requirement, so we'll use a good balance
        qr = qrcode.QRCode(
            version=1,  # Start with smallest version
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,  # Will be calculated
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Calculate box size to fit max_width
        qr_modules = qr.modules_count
        available_width = self.max_width - (qr.border * 2)
        optimal_box_size = max(1, available_width // qr_modules)
        
        # Recreate QR code with optimal box size
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=optimal_box_size,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Ensure the QR code doesn't exceed max_width
        if qr_img.width > self.max_width:
            ratio = self.max_width / qr_img.width
            new_height = int(qr_img.height * ratio)
            qr_img = qr_img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
        
        return qr_img
    
    def text_with_qr_to_image(self, text: str, qr_data: Optional[str] = None, is_markdown: bool = False) -> Image.Image:
        text_img = self.text_to_image(text, is_markdown)
        
        if qr_data:
            qr_img = self.generate_qr_code(qr_data)
            
            # Create combined image
            total_height = text_img.height + qr_img.height + self.padding
            combined_width = max(text_img.width, qr_img.width)
            
            combined_img = Image.new('RGB', (combined_width, total_height), 'white')
            
            # Paste text image at top
            combined_img.paste(text_img, (0, 0))
            
            # Paste QR code below text, centered
            qr_x = (combined_width - qr_img.width) // 2
            combined_img.paste(qr_img, (qr_x, text_img.height + self.padding))
            
            return combined_img
        
        return text_img