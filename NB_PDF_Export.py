import fitz #needs pip install PyMuPDF==1.23.3

from PIL import Image
import io
import os

rect_dict = {
'x0' : 0,
'y0' : 0,
'x1' : 0,
'y1' : 0
}


blankImg = r"C:\Users\9218\Documents\doublePageArticleSampl\double_stamp_test\blank.jpg"


#it doesn't deletes the existing thumbnail, rather over writes new thumbnails there
#uses pytpdf2
def CreateMultiThumbExportPyPDF2 (inputPDF, outputPDF, thumb_images:list, source_name, config):

    from PyPDF2 import PdfWriter, PdfReader
    import io
    from reportlab.pdfgen import canvas #, pdfimages
    from reportlab.lib.pagesizes import letter, A4

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4, enforceColorSpace='rgb') 
    
    dia_count = len(thumb_images)
    
    gap = config['dia_gap']
    dia_height = config['existing_dia']['height']
    dia_width = config['existing_dia']['width']

    dia_x0 = config['existing_dia']['x'] # -( dia_count-1)*(gap+dia_width)
    dia_y0 = config['existing_dia']['y'] 
    
   
    #using the blank image
    can.drawImage(blankImg, dia_x0, dia_y0, dia_height, dia_width)

    # can.drawImage(diaImg1, 306,666, 80, 110)
    # can.drawImage(diaImg2, 406,666, 80, 110)
    # can.drawImage(diaImg3, 506,666, 80, 110)
    print(thumb_images)
    #drawing the dia images
    for i in range(len(thumb_images)):  
        can.drawImage(thumb_images[i], dia_x0-( (dia_count-i-1)*(gap+dia_width)), dia_y0, dia_width, dia_height)


    source_x0 = config['source_logo']['x']
    source_y0 = config['source_logo']['y']
    source_logo_width = config['source_logo']['width']
    source_logo_height = config['source_logo']['height']

    source_logo_path = os.path.join(config['LOGO_DIR'], f'{source_name}.jpg')

    if os.path.exists(source_logo_path):
        can.drawImage(source_logo_path, source_x0, source_y0, source_logo_width, source_logo_height)
    else:
        source_x0 = config['source_text']['x']
        source_y0 = config['source_text']['y']
        source_width = config['source_text']['width']
        source_height = config['source_text']['height']
        source_fontname = config['source_text']['font_name']
        source_fontsize = config['source_text']['font_size']

        can.setFont(source_fontname, source_fontsize)
        can.drawString(source_x0, source_y0, source_name.upper())   

    can.save()


    #move to the beginning of the StringIO buffer
    packet.seek(0)
    watermark_pdf = PdfReader(packet) # watermark_pdf is never written to drive, it remains memory only

    existing_pdf = PdfReader(open(inputPDF, "rb"))

    output = PdfWriter()

    for page in existing_pdf.pages:
        page.merge_page(watermark_pdf.pages[0])
        output.add_page(page)

    # finally, write "output" to a real file
    output_stream = open(outputPDF, "wb")
    output.write(output_stream)
    output_stream.close()
    
    del watermark_pdf



class NbPDFExport_Fitz:

    """
    A class for exporting PDFs using PyMuPDF (Fitz).

    Attributes:
        doc: A PyMuPDF document object representing the PDF being worked on.
        inputPDF: The path to the input PDF file.
        conf: A dictionary containing configuration settings for the PDF export.

    Methods:
        __init__: Initializes the NbPDFExport_Fitz class with a configuration dictionary.
        insert_converted_image: Inserts a converted image into a PDF page at specified coordinates.
    """

    doc =None
    inputPDF = ''
    conf = {}


    def __init__(self: object, config: dict):

        """
        Initializes the NbPDFExport_Fitz class.

        Args:
            config (dict): A dictionary containing configuration settings.
        """
        self.doc =None
        self.conf = config
        self.doc = fitz.open()
        


    def insert_converted_image(self: object, pdf_page: object, image_path: str, coords: tuple, aspect_ratio: bool=True):

        """
        Inserts a converted image into a PDF page at specified coordinates.

        Args:
            pdf_page (object): The PDF page object where the image should be inserted.
            image_path (str): The path to the image file.
            coords (tuple): The coordinates (x1, y1, x2, y2) specifying the rectangle where the image should be inserted.
            aspect_ratio (bool, optional): Whether to maintain the aspect ratio of the image. Defaults to True.
        """
        
        def convert2jpg_rgb(input_path: str):
            # Open the image using Pillow
            image = Image.open(input_path)
            image.LOAD_TRUNCATED_IMAGES = True

            if image.mode == 'RGBA' or image.format == 'PNG' :
                if image.mode == 'P':
                    image = image.convert('RGBA')
                else:
                    image = image.convert('RGB')
            
            if image.mode == 'CMYK' and image.format == 'JPEG' :
                image = image.convert('RGB')

            # Convert Pillow image to bytes
            image_bytes = io.BytesIO()

            # resized_image.save(image_bytes, format="JPEG")  # You can adjust the format if needed
            if image.mode == 'RGBA':
                image.save(image_bytes, format="PNG")
            else:
                image.save(image_bytes, format="JPEG")

            image_bytes.seek(0)

            return image_bytes
        
        pdf_page.clean_contents()

        # Get the rectangle coordinates
        x1, y1, x2, y2 = coords
        rect = fitz.Rect(x1, y1, x2, y2)

        # Open the image using Pillow and resize it
        image_bytes = convert2jpg_rgb(image_path)

        # Convert Pillow image bytes to PyMuPDF Pixmap
        image_pixmap = fitz.Pixmap(image_bytes)

        # image_pixmap = fitz.Pixmap(image_path)  # The 0 denotes that it's reading from a memory buffer
        
        img_w = image_pixmap.w
        img_h = image_pixmap.h
        rect_w = rect.width
        rect_h = rect.height


        img_w_h_ratio = img_w / img_h
        rect_w_h_ratio = rect_w / rect_h

        resize_type = 1
       
        if img_w_h_ratio == rect_w_h_ratio: 

            pdf_page.insert_image(left_aligned_rect, pixmap=image_pixmap, keep_proportion=aspect_ratio)

        elif img_w_h_ratio < rect_w_h_ratio: # horz_center_alignement issue e.g. about pharma logo
            
            if img_w_h_ratio == 1.0:
                # Image is taller than the rectangle
                new_height = rect_h
                new_width = new_height * img_w_h_ratio

                # Center the image within the rectangle
                new_x0 = x1
                new_y0 = y1 + (rect_h - new_height) / 2
                new_x1 = new_x0 + new_width
                new_y1 = new_y0 + new_height

                rect = fitz.Rect(new_x0, new_y0, new_x1, new_y1)
                pdf_page.insert_image(rect, pixmap=image_pixmap, keep_proportion=aspect_ratio)

            else:
                placed_img_width = img_w_h_ratio * rect_h
                diff_width = abs(rect_w - placed_img_width)
                adjst_width = int(diff_width/2)

                left_aligned_rect = rect
                left_aligned_rect.x0 -= (adjst_width * resize_type)
                left_aligned_rect.x1 -= (adjst_width * resize_type)
                
                pdf_page.insert_image(left_aligned_rect, pixmap=image_pixmap, keep_proportion=aspect_ratio)
            
        elif img_w_h_ratio > rect_w_h_ratio: # vert_center_alignment issue e.g. il secolo di italia logo

            placed_img_height = rect_w / img_w_h_ratio
            diff_height = abs(rect_h - placed_img_height)
            adjst_height = int(diff_height/2)

            btm_aligned_rect = rect
            btm_aligned_rect.y0 += (adjst_height * resize_type)
            btm_aligned_rect.y1 += (adjst_height * resize_type)

            pdf_page.insert_image(btm_aligned_rect, pixmap=image_pixmap, keep_proportion=aspect_ratio)

            pdf_page.clean_contents()


    def add_image(self: object, image_path: str, x: int, y: int, width: int, height: int, tot_pages: int, aspect_ratio: bool=True):

        """
        Adds an image to the PDF.

        Args:
            image_path (str): The path to the image file.
            x (int): The x-coordinate of the top-left corner of the image.
            y (int): The y-coordinate of the top-left corner of the image.
            width (int): The width of the image.
            height (int): The height of the image.
            tot_pages (int): The total number of pages in the PDF.
            aspect_ratio (bool, optional): Whether to maintain the aspect ratio of the image. Defaults to True.

        Returns:
            None.
        """
        
        x0 = x
        y1 = y
        x1 = x0 + width
        y0 = y1 - height
        
        if self.doc != None:
           
            for page_no in range(tot_pages):
                page = self.doc[page_no]
                self.insert_converted_image(page, image_path, (x0,y0,x1,y1))


    def add_dias(self: object, dia_images: list, gap: int=3):

        """
        Adds diagrams to each page of the PDF.

        Args:
            dia_images (list): A list of paths to the diagram images.
            gap (int, optional): The gap between diagrams. Defaults to 3.

        Returns:
            None.
        """
        
        x= self.conf['new_dia_dict']['x']
        y= self.conf['new_dia_dict']['y']

        dia_count = len(dia_images)
        
        if self.doc != None:
            for page in self.doc:
                
                pdf_page_height = page.mediabox_size.y

                for i in range(len(dia_images)):
                    # image = fitz.open(dia_images[i])

                    # x0 = x + (i*gap) -dia_count*(int(self.conf['DiaJpgSize'][0]*72/300))
                    x0 = x - ( (dia_count-i-1)* (gap + self.conf['new_dia_dict']['width']) )

                    # x1 = x0 + int(self.conf['DiaJpgSize'][0]*72/300)
                    x1 = x0 + self.conf['new_dia_dict']['width']

                    
                    y1 = y  
                    # y1 = y0 + int(self.conf['DiaJpgSize'][1]*72/300)
                    y0 = y1 - self.conf['new_dia_dict']['height']

                    # y0 = pdf_page_height - y #converting to pdf co-ordinates 
                    # y1 = y0 - int(self.conf['DiaJpgSize'][1]*72/300)

                    #converting to pdf coordinates
                    x0_pdf = x0 
                    x1_pdf = x1 
                    y0_pdf = pdf_page_height -y1  #substracting with y0 would lead to invalid rect because y0 is bottom in pdf_cordinate
                    y1_pdf = pdf_page_height -y0 #where as y0 is top in image cordinate


                    # rect = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)
                    rect = fitz.Rect(x0, y0, x1, y1)
                    page.clean_contents()
                    page.insert_image(rect, filename=dia_images[i]) 

                    page.draw_rect(rect, fill=(1, 1, 1), fill_opacity=0)
                    
  

    def add_dias_one_by_one(self: object, dia_images: list, gap: int=3):

        """
        Adds diagrams one by one to each page of the PDF.

        Args:
            dia_images (list): A list of paths to the diagram images.
            gap (int, optional): The gap between diagrams. Defaults to 3.

        Returns:
            None.
        """
        
        x= self.conf['new_dia_dict']['x']
        y= self.conf['new_dia_dict']['y']

        dia_count = len(dia_images)
        
        if self.doc != None:
            for page in self.doc:
                # page = self.doc.load_page(0)

                pdf_page_height = page.mediabox_size.y

                for i in range(len(dia_images)):
                    # image = fitz.open(dia_images[i])

                    # x0 = x + (i*gap) -dia_count*(int(self.conf['DiaJpgSize'][0]*72/300))
                    x0 = x - ( (dia_count-i-1)* (gap + self.conf['new_dia_dict']['width']) )

                    # x1 = x0 + int(self.conf['DiaJpgSize'][0]*72/300)
                    x1 = x0 + self.conf['new_dia_dict']['width']

                    
                    y1 = y  
                    # y1 = y0 + int(self.conf['DiaJpgSize'][1]*72/300)
                    y0 = y1 - self.conf['new_dia_dict']['height']

                    # y0 = pdf_page_height - y #converting to pdf co-ordinates 
                    # y1 = y0 - int(self.conf['DiaJpgSize'][1]*72/300)

                    #converting to pdf coordinates
                    x0_pdf = x0 
                    x1_pdf = x1 
                    y0_pdf = pdf_page_height -y1  #substracting with y0 would lead to invalid rect because y0 is bottom in pdf_cordinate
                    y1_pdf = pdf_page_height -y0 #where as y0 is top in image cordinate


                    # rect = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)
                    rect = fitz.Rect(x0, y0, x1, y1)
                    page.clean_contents()
                    page.insert_image(rect, filename=dia_images[i]) # inserting mirror inverted image

                    page.draw_rect(rect, fill=(1,1,1), fill_opacity=0)
                    
                    # pix = fitz.Pixmap(dia_images[i])
                    # page.insert_image(rect, pixmap = pix) # inserting mirror inverted image

                    
                    # img_stream = open(dia_images[i], "rb").read()
                    # page.insert_image(rect, stream=img_stream) # inserting mirror inverted image

                    # img_stream = open(dia_images[i], "rb").read()

                    # Convert image file to pixmap

                    """ image = Image.open(dia_images[i])

                    # Mirror invert the image horizontally and vertically
                    image_Horz = image.transpose(Image.FLIP_LEFT_RIGHT)
                    image_hv = image_Horz.transpose(Image.FLIP_TOP_BOTTOM)

                    pix = fitz.Pixmap(fitz.csRGB, image_hv)
                    page.insert_image(rect, pixmap = pix) """ #

   
    def draw_meta_text_in_rect_new_pdf(self: object, x: int, y: int, width: int, height: int, text: str, font_name: str, font_size: int, font_file_path: str, tot_pages: int, text_color: tuple=(0,0,0)):
        
        """
        Draws meta text inside a rectangle on each page of the PDF.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
            text (str): The text to be drawn.
            font_name (str): The name of the font to be used.
            font_size (int): The font size.
            font_file_path (str): The path to the font file.
            tot_pages (int): The total number of pages in the PDF.
            text_color (tuple, optional): The color of the text as a tuple of RGB values. Defaults to (0,0,0).

        Returns:
            None.
        """
        
        if text != None:
           
            if font_file_path != '':

                font = fitz.Font(font_name, fontfile=font_file_path)
                # font = fitz.Font(fontfile=font_file_path)
                calc_width = font.text_length(text, fontsize=font_size)

                x0 = x
                y1 = y       
                x1 = x0 + width
                y0 = y1 - height
            
                for page_no in range(tot_pages):

                    page = self.doc[page_no]
                
                    if calc_width > width:    
                        font_size = font_size * width/calc_width
                        
                    page.clean_contents()
                    text_point = fitz.Point(x,y)
                    
                    page.insert_font(fontname=font_name, fontfile=font_file_path)
                    page.insert_text(text_point,text,fontname = font_name, fontfile=font_file_path, border_width=1, fontsize = font_size ,color = text_color)
                    
                    page.clean_contents()


    def draw_source_text_in_rect_new_pdf(self: object, x: int, y: int, width: int, height: int, text: str, font_name: str, font_size: int, font_file_path: str, tot_pages: int, text_color: tuple=(0,0,0)):

        """
        Draws text inside a rectangle on each page of the PDF.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
            text (str): The text to be drawn.
            font_name (str): The name of the font to be used.
            font_size (int): The font size.
            font_file_path (str): The path to the font file.
            tot_pages (int): The total number of pages in the PDF.
            text_color (tuple, optional): The color of the text as a tuple of RGB values. Defaults to (0,0,0).

        Returns:
            None.
        """
        
       
        if text != None:
           
            if font_file_path != '':

                font = fitz.Font(font_name, fontfile=font_file_path)
                # font = fitz.Font(fontfile=font_file_path)
                calc_width = font.text_length(text, fontsize=font_size)

                x0 = x
                y1 = y       
                x1 = x0 + width
                y0 = y1 - height
            
                for page_no in range(tot_pages):

                    page = self.doc[page_no]
                
                    if calc_width > width:    
                        font_size = font_size * width/calc_width
                        
                    page.clean_contents()
                    text_point = fitz.Point(x,y)
                    
                    page.insert_font(fontname=font_name, fontfile=font_file_path)
                    page.insert_text(text_point,text,fontname = font_name, fontfile=font_file_path, border_width=1, fontsize = font_size ,color = text_color)
                    
                    page.clean_contents()
                    
    
    def insert_xml_text_into_new_pdf(self: object, coordinates_info: list, tot_pages: int):

        """
        Inserts XML text into the PDF at specified coordinates on each page.

        Args:
            coordinates_info (list): A list containing information about text coordinates for each page.
                Each item in the list is a tuple containing (text, x0, y0, x1, y1) for each block of text.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """
        
        import fitz
        import os

        for page_no in range(tot_pages):
                        
            page = self.doc[page_no]

            page.clean_contents()

            block = coordinates_info[page_no]
            for words in block:
               
                text, x0, y0, x1, y1 = words
                
                x0 = (x0 * 72) / 300
                y0 = (y0 * 72) / 300
                x1 = (x1 * 72) / 300
                y1 = (y1 * 72) / 300

                font_size = 150   
                font = fitz.Font('Times-Roman')
                calc_width = font.text_length(text, fontsize=font_size)

                # Check if the text width exceeds the available width, and adjust font size accordingly
                width = x1-x0
                if calc_width > width:
                    font_size = font_size * width/calc_width
        
                page.clean_contents()
                text_point = fitz.Point(x0,y1)

                page.insert_font(fontname='Times-Roman')
                
                page.insert_text(text_point, text, fontname="Times-Roman", fontsize=font_size, color=(0, 0, 0), fill_opacity=0)
                page.clean_contents()


    def insert_article_text_into_new_pdf(self:object, coordinates_info: list, tot_pages: int):

        """
        Inserts article text into the PDF at specified coordinates on each page.

        Args:
            coordinates_info (list): A list containing information about text coordinates for each page.
                Each item in the list is a tuple containing (text, x0, y0, x1, y1) for each block of text.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """
        
        import fitz
        import os

        for page_no in range(tot_pages):
                        
            page = self.doc[page_no]
            # page = self.doc.new_page(width=595, height=842)

            page.clean_contents()

            block = coordinates_info[page_no]
            for words in block:
                
                text, x0, y0, x1, y1 = words
                
                x0 = (x0 * 72) / 300
                y0 = (y0 * 72) / 300
                x1 = (x1 * 72) / 300
                y1 = (y1 * 72) / 300

                if text.endswith("-") and not text.endswith(" -"):
                    text = text[:-1].replace("-", "") + "\u00AD"
                else:
                    text = text.replace("-", "")

                font_size = 150   
                font = fitz.Font('Times-Roman')
                calc_width = font.text_length(text, fontsize=font_size)

                # Check if the text width exceeds the available width, and adjust font size accordingly
                width = x1-x0
                if calc_width > width:
                    font_size = font_size * width/calc_width
        
                page.clean_contents()
                text_point = fitz.Point(x0,y1)

                page.insert_font(fontname='Times-Roman')
                page.insert_text(text_point, text, fontname="Times-Roman", fontsize=font_size, color=(0, 0, 0), fill_opacity=0)

                page.clean_contents()


    def insert_pdf_text_into_new_pdf(self: object, coordinates_info: list, tot_pages: int):

        """
        Inserts text into the PDF at specified coordinates on each page.

        Args:
            coordinates_info (list): A list containing information about text coordinates for each page. 
                Each item in the list is a list of tuples containing (x0, y0, x1, y1, text, block_no, block_type, i) for each word.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """
        
        import fitz
        import os

        for page_no in range(tot_pages):
                        
            page = self.doc[page_no]

            page.clean_contents()

            block = coordinates_info[page_no]
            for words in block:
                
                x0, y0, x1, y1, text, block_no , block_type,i = words

                font_size = 150   
                font = fitz.Font('Times-Roman')
                calc_width = font.text_length(text, fontsize=font_size)

                # Check if the text width exceeds the available width, and adjust font size accordingly
                width = x1-x0
                if calc_width > width:
                    font_size = font_size * width/calc_width
        
                page.clean_contents()
                text_point = fitz.Point(x0,y1)

                page.insert_font(fontname='Times-Roman')
                
                page.insert_text(text_point, text, fontname="Times-Roman", fontsize=font_size, color=(0, 0, 0), fill_opacity=0)
                page.clean_contents()
                

    def add_tif_img(self: object, image_list: list, tot_pages: int):

        """
        Adds TIFF images from a list to the PDF at specified locations on each page.

        Args:
            image_list (list): A list of paths to TIFF image files, one for each page of the PDF.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """
        import fitz  # PyMuPDF
        import io
        from PIL import Image

        for page_no in range(tot_pages):
            page = self.doc.new_page(width=595, height=842)
           

            # Open the image with PIL (Python Imaging Library)
            image = Image.open(image_list[page_no])

            #im_crop = im.crop((left, upper, right, lower))   (0, 537, 2481, 3273)
            cropped_image = image.crop((93, 537, 2481, 3305))  # Crop top-left quarter
            # We convert the image to 1 bit depth monochrome
            monochrome = cropped_image.convert('1')

            # We need to convert the image data to a bytes object
            imagebytes = io.BytesIO()
            monochrome.save(imagebytes, format='TIFF')
            imagebytes = imagebytes.getvalue()
                   
            image_pixmap = fitz.Pixmap(imagebytes)
            page.insert_image((20, 130, 595, 790), pixmap=image_pixmap)  #page.insert_image((18, 132, 595, 790), pixmap=image_pixmap)
    

    def add_ass_xml_img_obj(self: object, img_list: list, tot_pages: int):

        """
        Adds images from a list to the PDF at specified locations on each page.

        Args:
            img_list (list): A list of image information for each page. Each item in the list is a tuple containing:
                            (image_path: str, x0: int, y0: int, x1: int, y1: int), where
                            - image_path is the path to the image file,
                            - x0, y0, x1, y1 are the coordinates of the bounding rectangle for the image on the page.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """

        import fitz

        for page_no in range(tot_pages):
                                       
            page = self.doc[page_no]
           
            for img_info in img_list[page_no]:

                    img_obj, x0, y0, x1, y1= img_info

                    x0 = (x0 * 72) / 300
                    y0 = (y0 * 72) / 300
                    x1 = (x1 * 72) / 300
                    y1 = (y1 * 72) / 300

                    # rect = fitz.Rect(x0-3, y0-3, x1+3, y1+1)

                    rect = fitz.Rect(x0-2, y0-2, x1+2, y1+2)
                    annot = page.add_redact_annot(rect)

                    # Apply the redaction which removes the content in the defined area
                    page.apply_redactions()
                             
                    page.clean_contents()
                    page.insert_image((x0, y0, x1, y1), filename=img_obj, keep_proportion=True)


    def draw_line(self: object, x0: int, y0: int, x1: int, y1: int, tot_pages: int):


        """
        Draws a line on each page of the PDF.

        Args:
            x0 (int): The x-coordinate of the starting point of the line.
            y0 (int): The y-coordinate of the starting point of the line.
            x1 (int): The x-coordinate of the ending point of the line.
            y1 (int): The y-coordinate of the ending point of the line.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """

        for page_no in range(tot_pages):
                    
                    page = self.doc[page_no]

                    page.draw_line((x0,y0), (x1,y1), color=(0, 0, 0))
                    page.clean_contents()

                
    def add_copyright(self: object, image_path: str, x: int, y: int, width: int, height: int, tot_pages: int):


        """
        Adds a copyright image at a specified location on each page of the PDF.

        Args:
            image_path (str): The path to the copyright image file.
            x (int): The x-coordinate of the top-left corner of the copyright image.
            y (int): The y-coordinate of the top-left corner of the copyright image.
            width (int): The width of the copyright image.
            height (int): The height of the copyright image.
            tot_pages (int): The total number of pages in the PDF.

        Returns:
            None.
        """

        x0 = x
        y1 = y
        x1 = x0 + width
        y0 = y1 - height

        img = open(image_path, "rb").read()
        img_xref = 0        
        pixmap = fitz.Pixmap (image_path)
    

        if self.doc != None:
            rect = fitz.Rect(x0, y0, x1, y1)

            for page_no in range(tot_pages):
                page = self.doc[page_no]
                self.insert_converted_image(page, image_path, (x0,y0,x1,y1))


    def draw_blank_image_shape(self: object, x: int, y: int, width: int, height: int, fill_color: tuple=(1, 1, 1), opacity: int=1, tot_pages: int = 0):

        """
        Draws a blank image shape with a specified position, size, fill color, and opacity on each page of the PDF.

        Args:
            x (int): The x-coordinate of the top-left corner of the image shape.
            y (int): The y-coordinate of the top-left corner of the image shape.
            width (int): The width of the image shape.
            height (int): The height of the image shape.
            fill_color (tuple, optional): The fill color of the image shape, specified as an RGB tuple (default is (1, 1, 1)).
            opacity (int, optional): The opacity of the image shape, specified as an integer between 0 and 255 (default is 1).
            tot_pages (int, optional): The total number of pages in the PDF (default is 0).

        Returns:
            None.
        """

        rect = fitz.Rect(x, y, x+width, y+height)
        
        for page_no in range(tot_pages):

            page = self.doc[page_no]
            page.draw_rect(rect, fill=fill_color, color=fill_color, fill_opacity=opacity)
            page.clean_contents()


    def delete_existing_thumbnail(self: object, page_number: int, img_x: int, img_y: int, img_width: int, img_height: int):

        """
        Deletes an image from a PDF file at a specified location.

        Args:
            page_number (int): The page number of the image to delete.
            img_x (int): The x-coordinate of the top-left corner of the image.
            img_y (int): The y-coordinate of the top-left corner of the image.
            img_width (int): The width of the image.
            img_height (int): The height of the image.

        Returns:
            None.
        """
        import fitz
        if self.doc !=None:
        # for page_number in range(tot_pages):
            page = self.doc[page_number]
            # images = page.get_images()
            imageInfos = page.get_image_info(xrefs=True)
            for image_inf in imageInfos:
                if( (image_inf['bbox'][0]-img_x) < 1 and 
                    (image_inf['bbox'][3]-img_y) <1 and 
                    ((image_inf['bbox'][2]-image_inf['bbox'][0])-img_width) <1 and 
                    ((image_inf['bbox'][3] -image_inf['bbox'][1])-img_height) <1
                 ) :
                    page.delete_image(image_inf['xref'])
                    page.clean_contents()
                    
                    break


    def remove_text_in_rect(self: object, x: int, y: int, height: int, width: int):
        """
        Removes text within a specified rectangular area on the PDF page.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            height (int): The height of the rectangle.
            width (int): The width of the rectangle.
        """
        # rect = fitz.Rect(x0=x, y0=(y-height), x1=(x+width), y1=y)
        rcx0 = x
        rcx1 = x+width
        rcy0 = y+height
        rcy1 = y

        rect = fitz.Rect(rcx0, rcy0, rcx1, rcy1)


        if self.doc !=None:
            page = self.doc[0]
            page.clean_contents()            
            annot = page.add_redact_annot(rect) # Add a redaction annotation in the defined rectangular area            
            page.apply_redactions() # Apply the redaction which removes the text in the defined area
            page.clean_contents()
        
    def save_pdf(self: object, outputPDF: str):
        
        if self.doc:
            # self.doc.subset_fonts()
            self.doc.save(outputPDF,  garbage=4, clean = True, deflate = True, deflate_images = True, deflate_fonts = True)
            self.doc.close()
       
    def create_keyword_highlighted_pdf (self, hits, scope_area):

        import fitz
        # pip install PyMuPDF
        # don't do pip install fitz 
        # don't do pip install frontend
        # if fitz and frontend installed, kindly uninstall

        # Open the PDF file
        
        
        # Iterate through the pages of the PDF
        for page in self.doc:
            # Search for the text on the page
            for keyword in hits:
                areas = page.search_for(keyword, quads=True)
                # areas = page.search_for(keyword, hit_max=16, quads=True)
                # Highlight the text by creating an annotation for each area found
                for area in areas:
                    annot = page.add_highlight_annot(area)
                    annot.update() 

            # Save the modified PDF
            # doc.save(output_pdf)


    def highlight_words(input_pdf_path, output_pdf_path, hits):

        import PyPDF2

        pdf = PyPDF2.PdfFileReader(input_pdf_path)
        pdf_writer = PyPDF2.PdfFileWriter()

        for page_num in range(pdf.getNumPages()):
            page = pdf.getPage(page_num)
            page_text = page.extractText()
            for word_to_highlight in hits:
                if word_to_highlight in page_text:
                    page_text = page_text.replace(word_to_highlight, f'<span style="background-color: yellow;">{word_to_highlight}</span>')
            
            page.mergePage(page)
            pdf_writer.addPage(page)

        with open(output_pdf_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)

    # works on pymupdf==
    
### End of class NB_PDF_Export





# def highlight_word_pdflib(pdf_path, hits):

#     import pdfflib

#     """Highlights the given word in the given PDF file.

#     Args:
#     pdf_path: The path to the PDF file.
#     word: The word to highlight.
#     """

#     pdf = pdfflib.PdfFileReader(pdf_path)

#     for page in pdf.pages:
#         for text in page.get_text():
#             for word in hits:
#                 if word in text and text.isalpha():
#                     page.add_annotation(pdfflib.Annotation(text.bounds, pdfflib.Annotation.HIGHLIGHT))

# #     pdf.save(pdf_path)


if __name__ == "__main__":


    """ 
    This script processes a PDF file, adding or modifying content, and saves the modified PDF to a new file.

    It imports a module named `Setting` for configuration settings. The `Setting` module is assumed to contain necessary configuration data, but its contents are not provided in this snippet.

    The script defines paths to an input PDF file (`inputPDF`) and an output PDF file (`outputPDF`).

    It uses a class `NbPDFExport_Fitz` (not shown) to work with the input PDF file. This class is assumed to provide methods for processing PDFs.

    The script calls the following methods on the `NbPDFExport_Fitz` object:
    1. `delete_existing_thumbnail(0, 'Color_dia.jpg')`: Deletes an existing thumbnail image from the PDF. The parameters `0` and `'Color_dia.jpg'` are used to specify the page number and the name of the thumbnail image to delete, respectively.

    2. `add()`: [Description of the method is missing or incomplete. It seems to add something to the PDF, but the exact functionality is unclear from the provided snippet.]

    The modified PDF is then saved to the output PDF file path using the `save_pdf()` method of the `NbPDFExport_Fitz` object.

    Note: This docstring provides a high-level overview of the script's functionality based on the provided code snippet. The actual behavior of the script may vary depending on the implementation details of the `Setting` module and the `NbPDFExport_Fitz` class.
    """


    import Setting

    inputPDF = r"C:\Users\Newbase\Desktop\sifa_output\artices.pdf"
    outputPDF = r"C:\Users\Newbase\Desktop\sifa_output\output11.pdf"
    word = "hello"

    pdf_doc = NbPDFExport_Fitz(inputPDF)

    pdf_doc.delete_existing_thumbnail(0, 'Color_dia.jpg')
# pdf_doc.highlight_exact_keyword_adding_dia(outputPDF)
    pdf_doc.add
    pdf_doc.save_pdf(outputPDF)

    # highlight_word_pdflib(pdf_path, word)
    
    # highlight_exact_keyword_adding_dia(inputPDF, outputPDF, g_diaImges, dia_start_x=306 , dia_y=666 , hits=['la', 'hanno', 'tecnicamente', 'perché'], hits_scope_area=rect_dict)

    # create_keyword_highlighted_pdf(inputPDF, outputPDF, hits=['la', 'hanno', 'tecnicamente', 'perché'], scope_area=rect_dict)
    # highlight_words(inputPDF, outputPDF, hits=['la', 'hanno', 'tecnicamente', 'perché'])


    