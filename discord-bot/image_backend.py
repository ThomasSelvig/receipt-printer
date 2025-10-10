import re
import textwrap
from typing import Optional, Tuple
import qrcode
try:
    import markdown
except ImportError:
    markdown = None
from PIL import Image, ImageDraw, ImageFont


class ImageBackend:
    def __init__(self, max_width: int = 512, font_size: int = 24, line_spacing: int = 6):
        self.max_width = max_width
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.padding = 20
        self.bold_font = None
        self.h1_font = None
        self.h2_font = None
        self.h3_font = None
        
        font_loaded = False
        # Use fonts with better Unicode support (sans instead of mono for emojis)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Better Unicode support
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",  # Better Unicode support
            "/usr/share/fonts/truetype/ubuntu/UbuntuMono-Regular.ttf",
            "/System/Library/Fonts/Arial.ttf",  # macOS - better Unicode
            "/System/Library/Fonts/Monaco.ttf",  # macOS
        ]
        
        bold_font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Better Unicode support
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",  # Better Unicode support
            "/usr/share/fonts/truetype/ubuntu/UbuntuMono-Bold.ttf",
            "/System/Library/Fonts/Arial Bold.ttf",  # macOS
            "/System/Library/Fonts/Monaco.ttf",  # macOS
        ]
        
        # Load regular font
        for font_path in font_paths:
            try:
                self.font = ImageFont.truetype(font_path, self.font_size)
                font_loaded = True
                break
            except (IOError, OSError):
                continue
        
        # Load bold font
        for font_path in bold_font_paths:
            try:
                self.bold_font = ImageFont.truetype(font_path, self.font_size)
                break
            except (IOError, OSError):
                continue
        
        # Load header fonts (different sizes)
        # H1 - largest
        for font_path in font_paths:
            try:
                self.h1_font = ImageFont.truetype(font_path, int(self.font_size * 1.8))
                break
            except (IOError, OSError):
                continue
        
        # H2 - medium
        for font_path in font_paths:
            try:
                self.h2_font = ImageFont.truetype(font_path, int(self.font_size * 1.5))
                break
            except (IOError, OSError):
                continue
        
        # H3 - slightly larger than normal
        for font_path in font_paths:
            try:
                self.h3_font = ImageFont.truetype(font_path, int(self.font_size * 1.2))
                break
            except (IOError, OSError):
                continue
        
        # Fallback if no fonts loaded
        if not font_loaded:
            try:
                self.font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                self.font = ImageFont.load_default()
        
        # Set fallbacks if fonts failed to load
        if self.bold_font is None:
            self.bold_font = self.font
        if self.h1_font is None:
            self.h1_font = self.font
        if self.h2_font is None:
            self.h2_font = self.font
        if self.h3_font is None:
            self.h3_font = self.font
            
        # Try to load an emoji/symbol font as fallback
        self.emoji_font = None
        emoji_font_paths = [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf", 
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Has some symbols
            "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
        ]
        
        for font_path in emoji_font_paths:
            try:
                self.emoji_font = ImageFont.truetype(font_path, self.font_size)
                break
            except (IOError, OSError):
                continue
        
        if self.emoji_font is None:
            self.emoji_font = self.font
    
    def _draw_text_with_emoji_support(self, draw, position, text, font, fill='black'):
        """Draw text with emoji fallback support"""
        x, y = position
        
        # Try to render with main font first
        try:
            draw.text((x, y), text, fill=fill, font=font)
        except UnicodeEncodeError:
            # If main font fails, try character by character with emoji fallback
            current_x = x
            for char in text:
                try:
                    # Try main font first
                    draw.text((current_x, y), char, fill=fill, font=font)
                    bbox = font.getbbox(char)
                    char_width = bbox[2] - bbox[0]
                except (UnicodeEncodeError, OSError):
                    try:
                        # Fallback to emoji font
                        draw.text((current_x, y), char, fill=fill, font=self.emoji_font)
                        bbox = self.emoji_font.getbbox(char)
                        char_width = bbox[2] - bbox[0]
                    except (UnicodeEncodeError, OSError):
                        # Last resort: skip character or use replacement
                        char_width = font.getbbox('?')[2] - font.getbbox('?')[0]
                        draw.text((current_x, y), '?', fill=fill, font=font)
                
                current_x += char_width
    
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
    
    def _wrap_text(self, text: str, max_chars_per_line: int = 35) -> str:
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
        if markdown is None:
            # If markdown is not available, return text as-is
            return markdown_text
            
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
    
    def _parse_table(self, lines, start_idx):
        table_lines = []
        i = start_idx
        
        # Parse table lines
        while i < len(lines) and ('|' in lines[i] or lines[i].strip() == ''):
            if lines[i].strip():
                table_lines.append(lines[i])
            i += 1
        
        if len(table_lines) < 2:
            return [], start_idx + 1
        
        # Parse header
        header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
        
        # Skip separator line (assumed to be line 1)
        data_rows = []
        for row_line in table_lines[2:]:
            if row_line.strip():
                cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
                if cells:
                    data_rows.append(cells)
        
        # Calculate column widths
        all_rows = [header_cells] + data_rows
        col_widths = []
        for col_idx in range(len(header_cells)):
            max_width = max(len(row[col_idx]) if col_idx < len(row) else 0 for row in all_rows)
            col_widths.append(min(max_width + 2, 15))  # Max 15 chars per column
        
        # Format table
        formatted_table = []
        
        # Header with underline
        header_line = '|'.join(cell.ljust(width) for cell, width in zip(header_cells, col_widths))
        formatted_table.append({'text': header_line, 'font': self.bold_font})
        formatted_table.append({'text': '-' * len(header_line), 'font': self.font})
        
        # Data rows
        for row in data_rows:
            row_text = '|'.join(
                (row[col_idx] if col_idx < len(row) else '').ljust(width)
                for col_idx, width in enumerate(col_widths)
            )
            formatted_table.append({'text': row_text, 'font': self.font})
        
        return formatted_table, i
    
    def _parse_markdown_to_formatted_lines(self, markdown_text: str):
        lines = markdown_text.split('\n')
        formatted_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for table (line contains |)
            if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
                table_lines, next_i = self._parse_table(lines, i)
                formatted_lines.extend(table_lines)
                formatted_lines.append({'text': '', 'font': self.font})  # Add spacing after table
                i = next_i
                continue
            
            # Handle headers
            if line.startswith('# '):
                formatted_lines.append({'text': line[2:], 'font': self.h1_font})
            elif line.startswith('## '):
                formatted_lines.append({'text': line[3:], 'font': self.h2_font})
            elif line.startswith('### '):
                formatted_lines.append({'text': line[4:], 'font': self.h3_font})
            # Handle bold text (simple case - entire line)
            elif line.startswith('**') and line.endswith('**'):
                formatted_lines.append({'text': line[2:-2], 'font': self.bold_font})
            # Handle list items
            elif line.startswith('- ') or line.startswith('* '):
                formatted_lines.append({'text': '• ' + line[2:], 'font': self.font})
            elif re.match(r'^\d+\. ', line):
                # Numbered list - keep the number
                formatted_lines.append({'text': line, 'font': self.font})
            # Handle inline formatting (bold and italic mixed in text)
            elif '**' in line or '*' in line:
                # For now, just remove formatting markers and use regular font
                # This is a simplified approach - full markdown parsing would be more complex
                clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
                formatted_lines.append({'text': clean_text, 'font': self.font})
            else:
                # Regular text
                formatted_lines.append({'text': line, 'font': self.font})
            
            i += 1
        
        return formatted_lines
    
    def text_to_image(self, text: str, is_markdown: bool = False) -> Image.Image:
        if is_markdown:
            rendered_lines = self._parse_markdown_to_formatted_lines(text)
        else:
            rendered_lines = [{'text': line, 'font': self.font} for line in text.split('\n')]
        
        # Wrap text to fit receipt width and estimate size
        wrapped_lines = []
        total_height = 0
        max_width = 0
        
        for line_info in rendered_lines:
            if not line_info['text'].strip():
                wrapped_lines.append({'text': '', 'font': line_info['font']})
                bbox = line_info['font'].getbbox('A')
                line_height = bbox[3] - bbox[1]
                total_height += line_height + self.line_spacing
                continue
                
            # Wrap long lines
            wrapped = textwrap.fill(line_info['text'], width=35, break_long_words=False, break_on_hyphens=False)
            for wrapped_line in wrapped.split('\n'):
                wrapped_lines.append({'text': wrapped_line, 'font': line_info['font']})
                bbox = line_info['font'].getbbox(wrapped_line)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                max_width = max(max_width, line_width)
                total_height += line_height + self.line_spacing
        
        # Create image with padding
        img_width = min(self.max_width, max_width + self.padding * 2)
        img_height = total_height + self.padding * 2
        
        # Create white background image
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw text
        y_offset = self.padding
        for line_info in wrapped_lines:
            if line_info['text'].strip():
                self._draw_text_with_emoji_support(
                    draw, (self.padding, y_offset), line_info['text'], 
                    line_info['font'], fill='black'
                )
            
            bbox = line_info['font'].getbbox('A')  # Use a reference character
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
        # Convert qrcode wrapper to standard PIL Image
        qr_img = qr_img.convert('RGB')
        
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