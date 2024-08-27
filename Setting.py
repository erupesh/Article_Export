## copied from ExportCustomer


"""
Configuration settings for PDF export process.

This dictionary contains various settings and configurations for exporting PDFs. It includes settings for PDF size, maximum diameter limit, gap between diameters, paths to Poppler (a PDF rendering library) and font files, and other layout-related parameters. Additionally, it includes settings for logging, file naming conventions, metadata to be included in file names and XML exports, paths to various files and directories, and database connection details. There are also settings related to the XML template used, article export paths, and other specifics of the export process.

Attributes:
    PDF_Size (tuple): Tuple containing the dimensions of the PDF in points (width, height).
    MAX_DIA_LIMIT (int): Maximum diameter limit.
    DiaJpgSize (tuple): Size of the color_dia JPG images.
    dia_gap (int): Gap between diameters.
    source_logo (dict): Dictionary containing settings for the source logo.
    source_text (dict): Dictionary containing settings for the source text.
    top_cover (dict): Dictionary containing settings for the top cover.
    meta_dict (dict): Dictionary containing metadata settings.
    meta_font_file_path (str): Path to the metadata font file.
    ext_fontname (str): External font name.
    top_horz_line (dict): Dictionary containing settings for the top horizontal line.
    bottom_horz_line (dict): Dictionary containing settings for the bottom horizontal line.
    copy_right (dict): Dictionary containing settings for the copyright text.
    ...
    (other settings omitted for brevity)
"""


# pdf_cordintates and in points
exist_dia_dict = {
    'x': 467,
    'y': 126, # 715
    'width': 79,
    'height': 113
    
}

new_dia_dict = { #from export xml template multiplying 10 times*85/300 to convert to points
    'x': 479, # 1690/300*85=478.8 should be
    'y': 124,  # 440/300*85= 124.6 should be 
    'width': 90, # 320/300*85=90.6 i.e. 32 of xml file 320 mm 
    'height': 128 # 500/300*85=141.6 i.e. 50 of xml file 500 mm 
}

source_logo_dict = { #from export xml template multiplying 10 times*85/300 to convert to points
    'x': 28, # 100*85/300=28 
    'y': 55,  # 200*85/300=56 + HEIGHT 43 = 99
    'width': 250, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 43, # 150*85/300 i.e. 15 of xml file 150 mm
    'alignment': 'LEFT'
}

source_text_dict = { #from export xml template multiplying 10 times*85/300 to convert to points
    
    'x': 28, # 100*85/300=29
    'y': 55,  # 200*85/300=56.6
    'width': 283, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 43, # 150*85/300 i.e. 15 of xml file 150 mm
    'font_size': 18,
    "ext_fontname" : 'ArialBold',
    'font_file_path' :r"C:\WINDOWS\FONTS\ARIALBD.TTF",
    
}

top_cover_dict = { #from export xml template multiplying 10 times*85/300 to convert to points
    'x': 27, # 100*85/300=29 27 
    'y': 0,  # 200*85/300=56.6  60
    'width': 545, # 1000*85/300 i.e. 100 of xml file 1000 mm 450
    'height': 125 # 150*85/300 i.e. 15 of xml file 150 mm  65

}

meta_dict = {

    "Data:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 28, # 100*85/300=29
    'y': 76,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14, # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Date_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 82, # 100*85/300=29
    'y': 76,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Pag.:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 167, # 100*85/300=29
    'y': 76,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Page_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 218, # 100*85/300=29
    'y': 76,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Size:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 28, # 100*85/300=29
    'y': 90,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Size_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 82, # 100*85/300=29       # 53
    'y': 90,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "AVE:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 167, # 100*85/300=29
    'y': 90,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Ave_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 10,
    'x': 218, # 100*85/300=29
    'y': 90,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },
    
    "Tiratura:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 28, # 100*85/300=29
    'y': 102,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Publish_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 76, # 100*85/300=29
    'y': 102,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    
    "Diffusione:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 28, # 100*85/300=29
    'y': 110,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Circ_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 76, # 100*85/300=29
    'y': 110,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    
    "Lettori:" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 28, # 100*85/300=29
    'y': 119,  # 200*85/300=56.6
    'width': 48, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },

    "Red_field" : { #from export xml template multiplying 10 times*85/300 to convert to points
    'font_size': 8,
    'x': 76, # 100*85/300=29
    'y': 119,  # 200*85/300=56.6
    'width': 79, # 1000*85/300 i.e. 100 of xml file 1000 mm
    'height': 14 # 150*85/300 i.e. 15 of xml file 150 mm
    },
}

'''
# copied from .frm files for reference for easier undestanding
# these are in 1/10 mm unit
#A4 is 2100 x 2970      #in pdf points 595 x 842
FORMAT	=  (2159, 2794) #CUSTOM in pdf points 612 x 792

SOURCEBOXSIZE = (280 400)
SOURCEBOXSTART = (1650, 44) 

'''

top_horz_line_dict ={
    'x0' : 28,
    'y0' : 127,
    'x1' : 567,
    'y1' : 127
}

bottom_horz_line_dict ={
    'x0' : 28,
    'y0' : 794,
    'x1' :  567,
    'y1' : 794
}

copy_right_dict ={

    'x0' : 2,
    'y0' : 524,
    'width' :  70,
    'height' : 198
}

config_dict = {

    "PDF_Size" : (595, 842),
    'MAX_DIA_LIMIT' : 3,    
    'DiaJpgSize' : (331, 473), # #(280, 400) #79, 113 in color_dia JPG SIZE 331, 473 
    'dia_gap' : 2,
    # 'new_dia_size' : (90, 128), # not being used now  
    'existing_dia' : exist_dia_dict,
    'new_dia_dict': new_dia_dict,

    'source_logo': source_logo_dict,
    'source_text' : source_text_dict,
    'top_cover' : top_cover_dict,
    'meta_dict' : meta_dict,
    'meta_font_file_path' :r"C:\WINDOWS\FONTS\ARIAL.TTF",
    'ext_fontname' : 'Arial', 
    'top_horz_line' : top_horz_line_dict,
    'bottom_horz_line' : bottom_horz_line_dict,
    'copy_right' : copy_right_dict,
    

    'POPPLER_PATH': r"D:\NEWBASE\NEWBASE_PRINT\EXE_SIFA\poppler-23.07.0\Library\bin",

    # 'DSN' : 'sifa64',
    'DSN64' : 'sifa64',
    'DRIVES' : {},
    'drive_list' :  [],
    'doc_folder_name': '',

    #read settings
    'source' : r"D:\NEWBASE\NEWBASE_PRINT\Archives_SIFA\Articles\MultiDiaExport\Setting.py",

    ## Metadata appearing in file names (Articlel name will always be appended)
    # 'NAME_META_DATA'  :  ['SourceDate', 'SourceName', 'SourcePage'],
    'NAME_META_DATA'  :  ['SourceDate', 'PublicationNo'],

    'log_level': 'INFO', # can be anthing from these 6 items NOTSET, INFO, DEBUG, WARNING, ERROR, CRITICAL
    'log_folder': r'D:\Newbase\NEWBASE_PRINT\PythonScheduler\Log\ParallelExport',


    #date-format in filename (use only d,m,y
    'SOUCE_DATE_FORMAT' : "dd.mm.yyyy",
    'DATE_FILE_NAME_FORMAT' : "yymmdd",
    #
    ## Maximum file name length (<: 245)
    'FILE_NAME_LENGTH' : 150,
    #
    ## Metadata exported in the XML file. If empty ("[list]"), all fields will be exported
    ## except those having the NoExport flag set.
    'xml_meta_data' : [],
    'export_list' : [],
    #
    # XML Template used
    'FORMULAR': r"\\NITL-009494\NEWBASE-PR\Archives_sifa\editorial-system\form\articles.xml",
    'firstArticlePageArea': [],

    'ARTICLE_DES_PATH' : r"\\nitl-009494\NEWBASE-PR\Archives_SIFA\Articles\Articles.des",
    'LOGO_DIR': r"\\nitl-009494\NEWBASE-PR\Archives_SIFA\editorial-system\logos",
    #FORMULAR_base	""
    'FIELDFORMNAME' :  "FormName",
    #'CDF2XML'  :    r"D:\NEWBASE\NEWBASE_PRINT\EXE1_Test\cdf2xml.exe",
    'CDF2XML'  :    r"D:\NEWBASE\NEWBASE_PRINT\EXE_SIFA\cdf2xml.exe",

    'NEWBASEINI'   :   r'\\NITL-009494\NEWBASE-PR\exe_sifa\newbase.ini',

    'EXPORT_DIR' : r'\\NITL-009494\newbase-pr\ExportArticles\sifa',
    # 'ftp_dir' : r'\\NITL-009494\NEWBASE-PR\FTPRassegna',
    # 'fine_file' : r'\\NITL-009494\NEWBASE-PR\FTPRassegna',

    # 'ZIP_EXE' : r'D:\NEWBASE\NEWBASE_PRINT\EXE\7-Zip\7z.exe',
    'CUSTOMER_FIELD' : "KeywordGroup",

    'FIELDNAME_SOURCEDATE' : "SourceDate",
    'FIELDNAME_ARTICLENO' : "ArticleNo",
    'FIELDNAME_LANGUAGE' : "ArticleLanguage",
    'ARTICLE_TABLE' : "Articles",
    'EVALUATION_TABLE' : "Evaluation",
    'fieldnameKeywordGroup' : "KeywordGroup",
    'KEYWORD_TABLE' : "Keywords",
    'FIELDNAME_KEYWORD' : "Keyword",

    'article_columns' : []
    
}


 