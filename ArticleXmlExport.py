# Python version 3.8.0 
"""
Overview:
    This project processes articles based on certain conditions and exports them.
    It uses multiprocessing to parallelize the processing of articles.

Usage:
    py -3.8 main_script.py [-a] [-d] [-artls ART_LIST_STR]

Options:
    -a, --auto       Run in automatic mode to process records of today.
    -d, --debug      Run in debug mode to print values instead of logging.
    -artls ART_LIST_STR
                     Run in manual export mode, processing selected records
                     provided in ART_LIST_STR.

Requirements:
    - Setting module must define config_dict as conf.
    - Database module must be imported for database operations.
    - NB_PDF_Export module must be imported for article_pdf creation
    
Examples:
    Run in automatic mode:
        py -3.8 main_script.py -a

    Run in debug mode:
        py -3.8 main_script.py -d

    Run in manual mode with specific articles:
        py -3.8 main_script.py -artls "25 26"
"""

from queue import Empty
import psutil
import os
import sys
import glob
import datetime
import multiprocessing
import logging
import re
import configparser
from lxml import etree
import pdf2image 
import time
import shutil

from Database import DbOperation

# import DbOperation
# import Oldtcl_nbPDFCreation
# import pdf2jpg

script_path = r"\\servernew-3\newbase-pr\Archives_SIFA\Articles\sifa_ExportScripts"
sys.path.append(script_path)

import NB_PDF_Export
# # should not import it here, since paracellel processes, don't get its updated values.
# from Setting import config_dict as conf 

max_artilce_limit = 30   # the maximum number of articles allowed
max_process_limit = 3    # the maximum number of processes allowed

# class ArticleExport:
#     doc_folder_name = '',
#     def __init__(self) -> None:
#         pass



rect_dict = {
'x0' : 0,
'y0' : 0,
'x1' : 0,
'y1' : 0
}



class Quad:

    """
    Represents a quadrilateral shape that outlines a word.

    Attributes:
    - text (str): The text content of the word.
    - top (int): The y-coordinate of the top edge of the quadrilateral.
    - bottom (int): The y-coordinate of the bottom edge of the quadrilateral.
    - left (int): The x-coordinate of the left edge of the quadrilateral.
    - right (int): The x-coordinate of the right edge of the quadrilateral.
    """

    def __init__(self) -> None:
        self.text = ""
        self.top = 0
        self.bottom = 0
        self.left = 0
        self.right = 0


class Word:

    """
    Represents a word in a document.

    Attributes:
    - text (str): The text content of the word.
    - quads (List[Quad]): A list of Quad objects representing the quadrilateral shapes outlining the word.
    - prevSeparator (str): The separator character before the word (if any).
    - separator (str): The separator character after the word (if any).
    """

    def __init__(self) -> None:
        self.text = ""
        self.quads = []
        self.prevSeparator = ''
        self.separator = ''
        

class WordXmlCreation:

    """
    A class for creating Word XML files from Region OCR XML files.
    """


    def __init__(self) -> None:

        """
        Initialize the WordXmlCreation object with default settings.
        """

        self.MergeSeparator = False
        self.keepSpace = False
        self.RemoveSoftHyphen = True

    def createWordXmlFromRgnOcrXml(self, strRegionOcrXmlPath: str, destFilePathWithoutExt: str, logger=None ):

        """
        Parse an XML file containing OCR data to create Word XML files.

        Args:
        - strRegionOcrXmlPath (str): The path to the XML file containing OCR data.
        - destFilePathWithoutExt (str): The destination file path without extension for the Word XML files.
        - logger (Logger, optional): A logger object for logging information. Default is None.

        Returns:
        - tuple: A tuple containing the total number of pages processed, the OCR text extracted, and the coordinates of each article line.
        """
        
        from codecs import xmlcharrefreplace_errors
        from logging import exception
        # from tkinter.ttk import Separator
        from lxml import etree
        import os

        pageCount = 0
        ocr_txt = ''
        
        try:
            if logger:
                logger.info ("Trying to read Region-ocr Xml file: " +strRegionOcrXmlPath)
            doc = etree.parse(strRegionOcrXmlPath)

            if logger:
                logger.info ("Dest file name recived is:"+ destFilePathWithoutExt)

            PageRegions = doc.xpath("region[@type='PageRef']")
            pageCount = len(PageRegions)

            if logger:
                logger.info ('Total Page count is: '+ str(pageCount) )
            # global articleWordCoordinates
            articleWordCoordinates = []
            pages = []
            prevLineWords = []
            prevPageWords = []

            article_line_coordinates = []
           
            for pageNo in range(pageCount):

                validCurPageRegionXpath = "region[@page='"+ str(pageNo) +"']"
                validLineXpath = ""
                regions = doc.xpath(validCurPageRegionXpath)
                
                if logger:
                    logger.info ("\nTotal region count in Page: " +str(pageNo)+ " is :" +str(len(regions)))

                # curPage = Page()
                # pages.append(curPage)
                curPageWords = []
             
                page_line_coords = []
                
                for region in regions:
                    
                    regionChildren = region.getchildren()    
                      
                    for lineNode in [node for node in regionChildren if node.tag=='line']:
                        
                        page_line_coords.append(tuple((lineNode.attrib['text'], int(lineNode.attrib['x0']),int(lineNode.attrib['y0']), int(lineNode.attrib['x1']), int(lineNode.attrib['y1']))))
                       
                        curLineWords = []            
                        curLineWords.clear()

                        lineChildren = lineNode.getchildren()
                        prevWord = None

                        for lineChild in lineChildren:
                            
                            if lineChild.tag=='word':
                             
                                curWordNode = lineChild

                                quad = Quad()
                                quad.left = curWordNode.attrib['x0']
                                quad.right = curWordNode.attrib['x1']
                                quad.top = curWordNode.attrib['y0']
                                quad.bottom = curWordNode.attrib['y1']

                                word = Word()
                                word.quads.clear()
                                word.quads.append (quad)
                                word.text = curWordNode.text
                                
                                prevSeparatorNode  = curWordNode.getprevious()
                                                             
                                if prevSeparatorNode != None and prevSeparatorNode.tag=='separator' and prevSeparatorNode.getparent()==lineNode:

                                    if 'sep' in prevSeparatorNode.attrib:
                                        word.prevSeparator = prevSeparatorNode.attrib['sep']

                                        if prevWord and prevWord.separator != word.prevSeparator:
                                            ocr_txt += word.prevSeparator
                                      
                                        # if self.keepSpace==False and word.prevSeparator == ' ':
                                        #     word.prevSeparator = ''
                        
                                        # if self.MergeSeparator:
                                        #     word.text += word.prevSeparator

                                separatorNode  = curWordNode.getnext()
                                if separatorNode != None and separatorNode.tag=='separator':
                                    if 'sep' in separatorNode.attrib:
                                        word.separator = separatorNode.attrib['sep']
                                        # ocr_txt += word.separator
                                        
                                        if self.keepSpace==False and word.separator == ' ':
                                            word.separator = ''

                                        # if self.MergeSeparator:
                                        #     word.text += word.separator

                                #soft-hyphen removal
                                if len(prevLineWords)>0 and prevLineWords[-1].separator == '-' :
                                   
                                    if len(curPageWords) >0:

                                        #dehcurPageWordsyphenating
                                        curPageWords[-1].text = curPageWords[-1].text.rstrip('-')
                                        #merging with first part of word
                                        curPageWords[-1].text += word.text
                                        #adding 2nd quadline to word
                                        curPageWords[-1].quads.append(quad)

                                    elif len(curPageWords)==0 and len(prevPageWords) >0:

                                        #dehcurPageWordsyphenating
                                        prevPageWords[-1].text = curPageWords[-1].text.rstrip('-') 
                                        #merging with first part of word
                                        prevPageWords[-1].text += word.text

                                        #can't add 2nd quadline to word since the Area doesn't present in prevPage
                                        #prevPageWords[-1].quads.append(quad)

                                    prevLineWords.clear()
                                    # not appending the current word since its merged with prevWord

                                    continue 
                                    
                                # curPage.words.append(word)
                                curPageWords.append(word)

                                curLineWords.append(word)
                                
                                ocr_txt += word.text
 
                                if len(curLineWords) > 1 and word.separator =='':
                                    ocr_txt += ' '
                                else:
                                    ocr_txt += word.separator
                                
                                prevWord = word
                    
                        prevLineWords.clear()
                        prevLineWords = curLineWords
                       
                        # ocr_txt += '\n'
                        #end of currentLineNode
                    
                    if region.attrib['type'] not in ['Dia', 'AreaRef', 'PageRef', 'Foto']:
                        
                        ocr_txt += '\n'
                        
                    prevPageWords = curPageWords
                    #end of currentPage Parsing
               
                article_line_coordinates.append(page_line_coords)

                if logger:
                    logger.info ("Total no of words in current page is = " +str(len(curPageWords)))
                wordfilePath = destFilePathWithoutExt + '_' + str(pageNo+1) + ".xml"

                lineEnd = '\n'
                docStart = "<document version=\"1\">" +lineEnd
                pageStart = "<page width=\"2483\" height=\"3522\">" + lineEnd
                wordstart = "<word text=\""
                wordend = "\" dict=\"true\">" +lineEnd
                wordclose = "</word>" + lineEnd
                pageclose = "</page>" + lineEnd
                docclose = "</document>"
                
                xmlContent = docStart
                xmlContent += pageStart
                currrent_page_words = []
                for word in curPageWords:
                    
                    xmlContent

                    wordline  = wordstart + word.text + wordend #wordend already Has lineEnd

                    quadline = '<quad l="' + str(word.quads[0].left)  
                    quadline += '" r="' + str(word.quads[0].right)
                    quadline += '" t="' + str(word.quads[0].top) 
                    quadline += '" b="'+ str(word.quads[0].bottom)+'"/>' + lineEnd

                    x0 = word.quads[0].left
                    x1 = word.quads[0].right
                    y0 = word.quads[0].top
                    y1 = word.quads[0].bottom
                   
                    if len(word.quads)==2:
                        quadline += '<quad l="' + str(word.quads[1].left)  
                        quadline += '" r="' + str(word.quads[1].right)
                        quadline += '" t="' + str(word.quads[1].top) 
                        quadline += '" b="'+ str(word.quads[1].bottom)+'"/>' + lineEnd
                        x0 = word.quads[1].left
                        x1 = word.quads[1].right
                        y0 = word.quads[1].top
                        y1 = word.quads[1].bottom

                    xmlContent += wordline 
                    xmlContent += quadline
                    xmlContent += wordclose
                    currrent_page_words.append(tuple((word.text, int(x0), int(y0), int(x1), int(y1))))
               
                xmlContent += pageclose
                xmlContent += docclose
                f = None
                try :
                    if logger:
                        logger.info ("Page file name is :"+ wordfilePath)  

                    f=open(wordfilePath, 'w', encoding='UTF-8')
                    f.write(xmlContent)
                   
                    articleWordCoordinates.append(currrent_page_words)
                    f.close()
                    f = None
                except exception as fileWriteErr:
                    if logger:
                        logger.exception ("FileWrite Error: " + str(fileWriteErr))
                    if f != None:
                        f.close()
                
                # ocr_txt += '\n' page break new line should come in region break new line only

                # end of currentPage
                                              
            # end of all pages

        except exception as err:
            logger.exception ("Error : "+ str(err))   

        return pageCount, ocr_txt, article_line_coordinates
    

def get_article_text(strRegionOcrXmlPath: str, logger=None):   # get artcile text from ocr tmp file

    """
    Parse an XML file containing OCR data to extract and return the text of the article.

    Args:
    - strRegionOcrXmlPath (str): The path to the XML file containing OCR data.
    - logger (Logger, optional): A logger object for logging information. Default is None.

    Returns:
    - str: The text of the article extracted from the OCR data.
    """
        
    from codecs import xmlcharrefreplace_errors
    from logging import exception
    # from tkinter.ttk import Separator
    from lxml import etree
    import os

    pageCount = 0
    article_txt = ''

    try:
        if logger:
            logger.info ("Trying to read Region-ocr Xml file: " +strRegionOcrXmlPath)
        doc = etree.parse(strRegionOcrXmlPath)

        PageRegions = doc.xpath("region[@type='PageRef']")
        pageCount = len(PageRegions)

        if logger:
            logger.info ('Total Page count is: '+ str(pageCount) )

        # global articleWordCoordinates

        previousLineWords = []
        previousPageWords = []

        for pageNo in range(pageCount):

            validCurPageRegionXpath = "region[@page='"+ str(pageNo) +"']"
            regions = doc.xpath(validCurPageRegionXpath)
            
            # curPage = Page()
            # pages.append(curPage)
            currentPageWords = []
           
            for region in regions:
                
                regionChildren = region.getchildren()    
                
                for lineNode in [node for node in regionChildren if node.tag=='line']:
                    
                    currentLineWords = []            
                    currentLineWords.clear()

                    lineChildren = lineNode.getchildren()
                    previousWord = None

                    i = 0
                    for lineChild in lineChildren:
                        
                        if lineChild.tag=='word':
                            
                            i += 1
                            
                            currentWordNode = lineChild

                            quad = Quad()
                            quad.left = currentWordNode.attrib['x0']
                            quad.right = currentWordNode.attrib['x1']
                            quad.top = currentWordNode.attrib['y0']
                            quad.bottom = currentWordNode.attrib['y1']

                            word = Word()
                            word.quads.clear()
                            word.quads.append (quad)
                            word.text = currentWordNode.text

                            previousSeparatorNode  = currentWordNode.getprevious()
                                                        
                            if previousSeparatorNode != None and previousSeparatorNode.tag=='separator' and previousSeparatorNode.getparent()==lineNode:
                                
                                if 'sep' in previousSeparatorNode.attrib:
                                    word.prevSeparator = previousSeparatorNode.attrib['sep']
                                    
                                    if previousWord and previousWord.separator != word.prevSeparator:
                                        article_txt += word.prevSeparator
                                    
                            separator_node  = currentWordNode.getnext()
                            if separator_node != None and separator_node.tag=='separator':
                                if 'sep' in separator_node.attrib:
                                    word.separator = separator_node.attrib['sep']
                                    
                            #soft-hyphen removal
                            if len(previousLineWords)>0 and previousLineWords[-1].separator == '-' :
                            
                                if len(currentPageWords) >0:

                                    #dehcurPageWordsyphenating
                                    currentPageWords[-1].text = currentPageWords[-1].text.rstrip('-')
                                    #merging with first part of word
                                    currentPageWords[-1].text += word.text
                                    #adding 2nd quadline to word
                                    currentPageWords[-1].quads.append(quad)

                                elif len(currentPageWords)==0 and len(previousPageWords) >0:

                                    #dehcurPageWordsyphenating
                                    previousPageWords[-1].text = currentPageWords[-1].text.rstrip('-') 
                                    #merging with first part of word
                                    previousPageWords[-1].text += word.text

                                    #can't add 2nd quadline to word since the Area doesn't present in prevPage
                                    #prevPageWords[-1].quads.append(quad)

                                previousLineWords.clear()
                                # not appending the current word since its merged with prevWord
                                
                                if article_txt.endswith('\n'):
                                    
                                    if word.text[0].isupper():
                                        article_txt += word.text
                                        article_txt += word.separator
                                    else:
                                        article_txt = article_txt[0:-2]
                                        article_txt += word.text
                                        article_txt += word.separator

                                elif word.text[0].isnumeric():
                                    article_txt += ' '
                                    article_txt += word.text
                                    article_txt += word.separator

                                elif word.text[0].isupper(): 
                                    article_txt += ' '
                                    article_txt += word.text
                                    article_txt += word.separator

                                else :
                                    article_txt = article_txt[0:-1]
                                    article_txt += word.text
                                    article_txt += word.separator
                                
                                continue 
                                
                            # curPage.words.append(word)
                            currentPageWords.append(word)

                            currentLineWords.append(word)
                            
                            article_txt += word.text
                           

                            if len(currentLineWords) > 1 and word.separator =='':
                                article_txt += ' '

                            else:
                                
                                if word.separator != ' -':
                                    article_txt += word.separator

                                if word.separator == ' -':
                                    article_txt += ' '

                            if len(currentLineWords) == 1 and word.separator =='' :
                                article_txt += ' '

                            previousWord = word

                        elif i == 0 and lineChild.tag == 'separator':
                            if article_txt.endswith('-'):
                                article_txt += ' '
                            article_txt += lineChild.attrib['sep']

                    if article_txt[-1] in ['.', '\'', ',', '"', '&', '%', ':', '?', '#', ';', ')', '!', '@']:
                        article_txt += ' '

                    previousLineWords.clear()
                    previousLineWords = currentLineWords
                
                if region.attrib['type'] not in ['Dia', 'AreaRef', 'PageRef']:
                         
                    if len(article_txt)>=1 and article_txt[-1].isspace():
                        article_txt = article_txt[0:-1]    
                    article_txt += '\n'

    except exception as err:
            logger.exception ("Error : "+ str(err)) 

    if article_txt[-1].isspace():
        article_txt = article_txt[0:-1]

    return article_txt


def parse_article_des_for_NoExpColumns(file_path: str):

    """
    Parse an article description file to extract column names that do not have the "NoExport" flag set.

    Args:
    - file_path (str): The path to the article description file.

    Returns:
    - List[str]: A list of column names that do not have the "NoExport" flag set.
    """

    column_names = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('=NAME='):
                column_name = line.split('=')[2]
            elif line.startswith('=FLAGS='):
                flags = line.split('=')[2].split(',')
                stripped_flags = [flg.strip() for flg in flags]
                if len(stripped_flags) >0:
                    if 'NoExport' not in stripped_flags:                        
                        column_names.append(column_name)
    return column_names


def process_article(article: object, conf: dict, db_column_list, log_folder_path: str, error_folder_path: str, DEBUG=False):

    """
    Process an article object, performing various operations such as PDF creation, OCR, and metadata extraction.

    Args:
    - article (object): The article object to process.
    - conf (dict): A dictionary containing configuration parameters.
    - db_column_list (list): A list of column names for the database.
    - log_folder_path (str): The path to the folder where log files will be saved.
    - error_folder_path (str): The path to the folder where error files will be saved.
    - DEBUG (bool, optional): Whether to run in debug mode. Defaults to False.

    Returns:
    - None
    """

    import shutil
    import re
    import logging

    DoHighlighting = False

    err_list = []
    export_dia_images = []
    
    articleno = article.ArticleNo
    pubno = article.PublicationNo
    print(f"processing article {articleno}")

    xmlMetadata = conf['xml_meta_data']

    # print("\nArticleXMLExport\n")
    if xmlMetadata == []:
        xmlMetadata = conf['export_list']

    if os.path.exists(conf['log_folder'])==False:
        print("Log folder doesn't exist: " + conf['log_folder'])
        if os.makedirs(conf['log_folder'])==False:
            print('Could not create log folder')
            return

    systemTime = datetime.datetime.now()

    if 'AutoExp' in log_folder_path:
        log_file_name =  articleno + '_' + systemTime.strftime('%H_%M_%S') + '_art_' + '.log'
    else:
        log_file_name = articleno + '_' +systemTime.strftime('%d-%m-%Y-%H_%M_%S') + '_Manual_Exp.log' 

    art_log_path = os.path.join(log_folder_path, log_file_name)   
    
    # Create and configure logger
    # logging.basicConfig(filename=art_log_path, format='%(asctime)s %(message)s', filemode='a')
    logger = logging.getLogger()
    logger.setLevel(conf['log_level'])

    # Create a file handler
    file_handler = logging.FileHandler(art_log_path)

    if DEBUG:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(conf['log_level'])  # Set the logging level

    # Create a stream handler for stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.ERROR)  # Set the logging level

    # Create a formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s %(message)s')

    # Set the formatter for the handlers
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    db = DbOperation(conf['DSN'], logHangle= logger)

    try:
        logger.info(f"\n\nprocessing article {articleno}")
        
        db.update_field("Articles", column='Send', value= 1, condColumn='ArticleNo', condValue= article.ArticleNo)
        # db.update_field("Articles", column='ExportInfo', value= f'MultiDia_{log_file_name}', condColumn='ArticleNo', condValue= article.ArticleNo)
        # db.update_record("Articles", column_value_dict={'Send':1, 'ExportInfo':f'MultiDia_{log_file_name}'}, condColumn='ArticleNo', condValue= article.ArticleNo)
        custinfo = ""
        rseval = db.search_table("Evaluation", f"ArticleNo='{articleno}'")
        if len(rseval) == 0 or len(rseval[0])==0:
            
            db.update_field("Articles", column='Send', value= 40, condColumn='ArticleNo', condValue= article.ArticleNo)
            logger.info("Article has no evaluation information or no topic so skipping.")
            
            return

        for eval in rseval:
            
            GrpID = eval.GrpID
            # keywordGroup = eval.KeywordGroup

            rscust = db.search_table("CUSTOMERThemes", f"GrpID='{GrpID}'", sortBy="ThemeOrder")

            for cust in rscust:
                strCustomerID = ' {:0>9}'.format(cust.CustomerID)
                rscustpub1 = db.search_table("CustomerPubs", f"CustomerID='{cust.CustomerID}'")
                if len(rscustpub1) > 0:
                    rscustpub2 = db.search_table("CustomerPubs", f"CustomerID='{cust.CustomerID}' and PublicationNo='{pubno}'")
                    if len(rscustpub2) == 0:
                        continue
                custRS = db.search_table("CLIENTI", f"IDCLIENTE='{cust.CustomerID}'")
                if len(custRS) == 0:
                    continue
                custRec = custRS[0]
                IsMultipleThemeNameInExportXml = custRec.MultipleThemeNameInExportXml
                custThemesInfo = ""
                custThemeList = []
                LowestThemeOrder = 99999
                for eval2 in rseval:
                    GrpID2 = eval2.GrpID
                    rstheme = db.search_table("CUSTOMERThemes", f"GrpID='{GrpID2}' and CustomerID='{cust.CustomerID}'", sortBy="ThemeOrder")
                    for themeRec in rstheme:
                        if IsMultipleThemeNameInExportXml != 1:
                            ThmOrder = themeRec.ThemeOrder
                            if ThmOrder == None:
                                ThmOrder = 0

                            if LowestThemeOrder > ThmOrder:
                                custThemesInfo = themeRec.Theme
                                LowestThemeOrder = ThmOrder
                        else:
                            if themeRec.Theme not in custThemesInfo:
                                custThemesInfo += f"{themeRec.Theme}; "
                                custThemeList.append(themeRec.Theme)

                if str(strCustomerID) not in custinfo:
                    if IsMultipleThemeNameInExportXml == 1:
                        custThemesInfo = custThemesInfo.strip("; ")
                    custinfo += f"    <Customer ID=\"{strCustomerID}\" Theme=\"{custThemesInfo}\" />"

        metadata = []
        for meta in conf['NAME_META_DATA']:
            ci = db_column_list['Articles'].index(meta)

            if type(article[ci]) == datetime.datetime:            
                metadata.append(str(article[ci].date().strftime("%d.%m.%Y")))
            else:
                metadata.append(str(article[ci]))
                
        destFile = "_".join(metadata)
        destFile = re.sub(r"[/\\:%*?\"<>|\t\n]", "+", destFile)[:conf['FILE_NAME_LENGTH']]
        destFile += f"_{article.ArticleNo}"

        # article.set_variables
        # artFolderPath = drive + abs_path_withoutfilename
        articleDrive = getCurrentDrive(conf['drive_list'], article.Volume)
        docFolderPath = os.path.join(conf['drive_list'][articleDrive], conf['doc_folder_name']) 
        artFolderPath = os.path.join(docFolderPath, article.DocPath)

        ave = article.Rate

        """ resultPDF = 0

        # PDFCreation.create_PDFFile(article, ave)

        if resultPDF == 0:
            logger.error("Error creating PDF file - mark article as send 50")
            old = {"ArticleNo": article.ArticleNo}
            new = {"Send": "50"}
            db.update_field("Articles", old, new)
            
            return

        try:
            shutil.copy(os.path.join(artFolderPath, "articles.pdf"), os.path.join(conf['EXPORT_DIR'], f"{destFile}.pdf"))
        except Exception as err:
            logger.exception(f"Could not copy PDF file: {err}") """
        
        # pdf creation starts
        input_art_pdf = os.path.join(artFolderPath, "articles.pdf")
        output_pdf = os.path.join(conf['EXPORT_DIR'], f"{destFile}.pdf")
        # srcPaperPageCount = len(article.SourcePage)
        # srcName = article.SourceName

        # create XML file with words and coordinates
        logger.info( "create coordinates file (.xml)")

        # it will create the ocr files if not present
        check_and_create_ocr_files(artFolderPath)

        resultOCR = 0
        errorOCR = ""
        ocr_text = ""
        resultOCR, errorOCR, ocr_text, articleLineCoordinates, pageCount = create_OCRxmlFile(conf['CDF2XML'], artFolderPath, conf['EXPORT_DIR'], destFile, logger)

        ass_xml_images, is_having_dia = parse_asmbl_xml4image_list(strFolderPath=artFolderPath, logger=logger,)


        src_pages = article.SourcePage
        src_pages_list = src_pages.split(',')

        if DoHighlighting == True:
            hitFile = os.path.join(artFolderPath, "00000001.hit")
            hits = ""

            # keywordGroup = article.fieldnameKeywordGroup
            keywordGropRecs = db.search_table(conf['EVALUATION_TABLE'], 'ArticleNo='+articleno )
            keywordGroup = keywordGropRecs[0].keywordgroup #taking first keywordgroup only

            if os.path.exists(hitFile):
                with open(hitFile, 'r', encoding='unicode') as fileHandle:
                    for line in fileHandle:
                        line = line[1:]  # Remove the first character '<'
                        pos = line[:line.find('<')].strip()  # Position of the next '<'
                        synonym = line[:pos]  # Synonym
                        group = line[pos + 1:]  # Keywordgroup
                        if keywordGroup == group:
                            if not re.search(synonym, hits, re.IGNORECASE):
                                hits += synonym + ","

                hits = hits.rstrip(",")
                logger.info(f"    hits: {hits}")
                # metas["found_hits"] = hits

            # dia_images = ParseSourceXml2DrawOnPDF(strFolderPath=artFolderPath, logger=logger, conf=conf,  dia_imges=export_dia_images, kw_hits=hits)
            dia_images = check_and_create_dia_images(strFolderPath=artFolderPath, logger=logger, conf=conf, is_having_dia=is_having_dia, dia_imges=export_dia_images)
        else:
            # dia_images = ParseSourceXml2DrawOnPDF(strFolderPath=artFolderPath, logger=logger, conf=conf,  dia_imges=export_dia_images)
            dia_images = check_and_create_dia_images(strFolderPath=artFolderPath, logger=logger, conf=conf, is_having_dia=is_having_dia, dia_imges=export_dia_images)


        if dia_images == -1:   # if infosfullpage.xml is not there
            # logger.error("Error: ParseSourceXml2DrawOnPDF() failed")
            logger.error("Error: check_and_create_dia_images() failed")
            return  
        
        # ass_xml_images, is_having_dia = parse_asmbl_xml4image_list(strFolderPath=artFolderPath, logger=logger,)

        if ass_xml_images == -1:
            # logger.error("Error: ParseSourceXml2DrawOnPDF() failed")
            logger.error("Error: parse_asmbl_xml4image_list() failed")
            return 
        
        
        pdf_creation(dia_images, ass_xml_images, is_having_dia, articleLineCoordinates, pageCount, strFolderPath=artFolderPath, exportPDFPath=output_pdf, logger=logger, conf=conf, article_rec=article)
        
        # PDF creation Ends
    
        article_number = article.ArticleNo

        AutoAbstractRS = db.search_table("autoabstract", f"ArticleNo = '{article_number}'")
        db_column_list['autoabstract'] = [column[0] for column in db.cursor.description]
        AutoAbstractFieldIndex = db_column_list['autoabstract'].index("AutoAbstract")
        abstractStr = ""
        for AutoAbstract in AutoAbstractRS:
            abstractStr = AutoAbstract[AutoAbstractFieldIndex]

        fh = None
        try:
            fh = open(os.path.join(conf['EXPORT_DIR'], f"{destFile}.xml"), "w", encoding="utf-8")
            fh.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
            fh.write("<RecordList>\n")
            fh.write("  <Record>\n")

            for meta in xmlMetadata:
                ci = db_column_list['Articles'].index(meta)

                if article[ci]==None:
                    article[ci] = ''

                if meta == "abstract" or meta in ['SourceName', 'SourcePage', 'Circulation', 'Publishing', 'Readers', 'ArticleLanguage', 'Country', 'Title', 'Author']:
                         
                    fh.write(f"    <Field name=\"{meta}\"><![CDATA[{str(article[ci])}]]></Field>\n")

                elif type(article[ci])==datetime.datetime :
                    if 'Date' in meta or 'date' in meta or 'DATE' in meta:
                        date_time_str = article[ci].strftime("%d.%m.%Y")
                    elif 'Time' in meta or 'time' in meta or 'TIME' in meta:
                        time_str = article[ci].strftime("%H:%M:%S")
                        date_time_str = f" {time_str}"
                    else:
                         date_time_str = article[ci].strftime("%d.%m.%Y, %H:%M:%S")

                    fh.write(f"    <Field name=\"{meta}\">{date_time_str}</Field>\n")
                else:
                    fh.write(f"    <Field name=\"{meta}\">{str(article[ci])}</Field>\n")
            
            fh.write(f"{custinfo}\n")
            fh.write(f"    <Document name=\"{destFile}.pdf\" />\n")
            if abstractStr==None:
                abstractStr = '' 
            if abstractStr.startswith('...') and abstractStr.endswith('...'):
                fh.write(f"\t<Abstract><![CDATA[ {abstractStr} ]]></Abstract>\n")
            elif abstractStr.startswith('...') and not abstractStr.endswith('...'):
                fh.write(f"\t<Abstract><![CDATA[ {abstractStr}]]></Abstract>\n")
            elif abstractStr.endswith('...') and not abstractStr.startswith('...'):
                fh.write(f"\t<Abstract><![CDATA[{abstractStr} ]]></Abstract>\n")
            else:
                fh.write(f"\t<Abstract><![CDATA[{abstractStr}]]></Abstract>\n")
            fh.write("  </Record>\n")
            fh.write("</RecordList>\n")
        except Exception as err:
            logger.exception(f"Could not write XML file: {err}")
            err_list.append(err)
            

        finally:
            if fh:
                fh.close()

        # ARTICLE XML CREATION FINISHED
        # article pdf creation start
        
        logger.info("  Creating JPEG files..")
        logger.info(f"  pdf: {destFile}.pdf")
        logger.info(f"  exportdir: {conf['EXPORT_DIR']}")
        logger.info(f"  jpg: {destFile}_%02d.jpg")

        # pdffile = os.path.join(conf['EXPORT_DIR'], f"{destFile}.pdf")
        # pdffile = os.path.join(artFolderPath, "ARTICLES.pdf")

        if os.path.exists(output_pdf)==False:
            logger.info(f"Article PDF {output_pdf}  not found")
        else:
            time.sleep(2)
            
        try:  
            # using 150 dpi resolution for export
            exp_images = pdf2image.convert_from_path(output_pdf, dpi=150, poppler_path=conf['POPPLER_PATH']) 

            for i in range(len(exp_images)):        
                # Save pages as images in the pdf
                exp_images[i].save(os.path.join(conf['EXPORT_DIR'], f"{destFile}_%02d.jpg"%(i+1)), 'JPEG')

        except Exception as e:
            err_list.append(e)
            logger.exception(f"error converting pdf to jpg: {e}")
          

        jpgfiles = glob.glob(os.path.join(conf['EXPORT_DIR'], f"{destFile}_[0-9][1-9].jpg"))
        npage = 0

        # for jpg in jpgfiles:
        #     npage += 1
        #     try:
        #         shutil.copyfile(jpg, os.path.join(artFolderPath, f"000000_{npage}.jpg"))
        #     except Exception as e:
        #         logger.exception(f"Could not copy jpg file: {e}")
        #         err_list.append(str(e))
                
       
        
        if resultOCR == 0:
            # AGR: Hier besser Artikel auf error=1 setzen
            errorString = f"Error evaluating OCR file: {errorOCR}"
            # error $errorString
            logger.error(errorString)
            return

        logger.info(f"create text file (.txt) with char length {len(ocr_text)}" )

        # write text file
        try:
            
            with open(os.path.join(conf['EXPORT_DIR'], f"{destFile}.txt"), "w", encoding="utf-8") as fhtxt:
                STYLE_break = "\n"
                # fulltext = article.ocr.format(1, article.ocr, WORDWRAP="WIDTH=8000 IGNOREEMPTY")
                # fulltext = ocr_text.format(1, ocr_text, WORDWRAP="WIDTH=8000 IGNOREEMPTY")
                fhtxt.write(ocr_text)
                
            
        except Exception as e:
            logger.exception(f"Could not write txt file: {e}")
            err_list.append(str(e))
           

        # copy txt-file back to doc-folder
        logger.info(f"{os.path.join(conf['EXPORT_DIR'], f'{destFile}.txt')} to {os.path.join(artFolderPath, 'articles.txt')}")
        try:
            shutil.copyfile(os.path.join(conf['EXPORT_DIR'], f"{destFile}.txt"), os.path.join(artFolderPath, "articles.txt"))
        except Exception as e:
            logger.exception(f"file copy failed: err:{e} to:{os.path.join(artFolderPath, 'articles.txt')}")
            err_list.append(str(e))
            
    
        try:
            i = 0
            for dia in export_dia_images:
                
                if os.path.exists(dia):
                    shutil.copyfile(dia, os.path.join(conf['EXPORT_DIR'], f"{destFile}_%d.jpg"%(i+1)) )
                    i+=1
                    
            
        except Exception as err:
            logger.exception(f"Export Dia copy failed: err: {err} ")
            err_list.append(str(e))
           
        

        # create some data
        data = "this file is for SIFA to identify end of creation process of article export"
        fine_file_path = os.path.join(conf['EXPORT_DIR'], f'{destFile}.fine')

        if len(err_list)==0:
            try:
                # open file in write mode
                with open(fine_file_path, 'w') as finefile:
                    finefile.write(data)
            except Exception as e:
                logger.exception(f"Could not write fine-file: {str(e)}")
                err_list.append(e)
               
                
                # UpdateRecord Articles [array get old] [array get new]  # replace with equivalent Python code

            # copy finefile back to doc-folder
            logger.info(f"copying {fine_file_path} to {artFolderPath}00000001.fine")
            try:
                shutil.copy(fine_file_path, artFolderPath)

                # db.update_field("Articles", column='Send', value= 20, condColumn='ArticleNo', condValue= article.ArticleNo)
                db.update_record("Articles", column_value_dict={'Send':20, 'ExportInfo':f'MultiDia_{log_file_name}'}, condColumn='ArticleNo', condValue= article.ArticleNo)
                logger.info(f".fine file copy finished \n\n")
            except Exception as e:
                logger.exception(f"file copy failed: err:{str(e)} to:{artFolderPath}")
                err_list.append(e)
                


    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"Article No: {article.ArticleNo} Processing err:{str(err)} in line no: {exc_tb.tb_lineno} of file: {fname}")
        logger.exception(f"Article Processing err:{str(err)}")
        err_list.append(err)
        
            
        if DEBUG:
            raise err
    
    finally:
        if len(err_list)!=0:
            shutil.copy2(art_log_path, error_folder_path)

    err_list.clear()


def getArticleNumber4mVolume(volume: str):

    """
    Get the article number from the volume string.

    Args:
    - volume (str): The volume string containing the article number in binary format.

    Returns:
    - str: The article number in hexadecimal format.
    """


    print (volume)
    
    artNoBinaryStr = volume[12:22] #last 12th to 21th 10 characters
    artNoBinary =  int(artNoBinaryStr, 2)
    artNoHex = hex(artNoBinary)

    return str(artNoHex)

def getCurrentDrive(drivePaths: list, articleVolume: str):

    """
    Get the current drive ID based on the binary string in the article volume.

    Args:
    - drivePaths (list): A list of drive paths.
    - articleVolume (str): A binary string representing the article volume.

    Returns:
    - int: The drive ID as an integer.
    """

    driveID_BinaryStr = articleVolume[3:10]
    driveIDInt = int(driveID_BinaryStr, 2)
    
    return driveIDInt

    
def get_xml_meta_list(article_des_file: str):

    """
    Get a list of names without the "NoExport" flag from an article description file.

    Args:
        article_des_file (str): The path to the article description file.

    Returns:
        list: A list of names without the "NoExport" flag.
    """

    # Initialize a list to store names without the "NoExport" flag
    names_without_noexport = []

    # Open the file for reading
    with open(article_des_file, 'r') as file:
        lines = file.readlines()

    # Initialize variables to keep track of the current name and its flags
    current_name = None
    current_flags = []

    # Iterate through the lines in the file
    for line in lines:
        line = line.strip()
        if line.startswith('=NAME='):
            # If a new name is encountered, update the current_name and reset the flags
            if current_name is not None and 'NoExport' not in current_flags and len(current_flags) >0:
                names_without_noexport.append(current_name)
            current_name = line.split('=')[2].strip()
            current_flags = []
        elif line.startswith('=FLAGS='):
            # Parse the flags and store them in current_flags list
            flags = line.split('=')[2].strip().split(',')
            current_flags.extend(map(str.strip, flags))

    # Check the last name in the file
    if current_name is not None and 'NoExport' not in current_flags and len(current_flags) >0:
        names_without_noexport.append(current_name)

    # Print the list of names without the "NoExport" flag
    return names_without_noexport


def getDSN(config: object):

    """
    Get the DSN (Data Source Name) from the configuration object.

    Args:
        config (object): The configuration object.

    Returns:
        str: The DSN value if found, otherwise None.
    """

    if 'DATASOURCE' in config._sections or 'DATASOURCE' in config._sections :
        if 'dsn64' in config['DATASOURCE'] :
            dsn64 = config['DATASOURCE']['dsn64']
            print (dsn64)
            # if DatasourceConfig.lower() == 'true' :
            #     DsnConfig['dsn64'] = True
        else :
            print ("switch 'dsn64' not found in Config.ini")
        
        # if 'ocrLanguage' in config['DATASOURCE'] :
        #     AnalysisConfig['OcrLanguage'] = config['DATASOURCE']['ocrLanguage']
        # else :
        #         print ("switch 'ocrLanguage' not found in Config.ini")
    else :
        print ('section \'DATASOURCE\' not found in Config.ini')

    return dsn64


def get_drive_dict(config: object):

    """
    Get a dictionary of drive paths from the configuration object.

    Args:
        config (object): The configuration object.

    Returns:
        dict: A dictionary containing drive paths, filtered by keys containing 'drive'.

    """


    drives_dict_filtered = {}

    drives_dict_parsed ={}

    if 'DRIVES' in config:
        drives_dict_parsed = dict(config['DRIVES'])
        # Get the options (keys) and values in the 'DRIVES' section
        options = config.options('DRIVES')
        i=0
        for option in options:
            option_lower =  option.lower()
            if 'drive' in option.lower():
                i += 1
                drives_dict_filtered[f'DRIVE{i}'] = drives_dict_parsed[f'drive{i}']

        # else :
        #     print ("switch 'DRIVE1' not found in Config.ini")

        #getting drive info in form of dict instead of getting drive_list
        
    else :
        print ('section \'DRIVES\' not found in Config.ini')

    return drives_dict_filtered


def get_drive_list(config: object):

    """
    Get a list of drive paths from the configuration object.

    Args:
        config (object): The configuration object.

    Returns:
        list: A list of drive paths.

    """

    drive_list = []

    if 'DRIVES' in config._sections :
        if 'DRIVE1' in config['DRIVES'] :
            drive1 = config['DRIVES']['DRIVE1']
            print (drive1)
            drive_list.append(drive1)

        else :
            print ("switch 'DRIVE1' not found in Config.ini")

        #getting drive info in form of dict instead of getting drive_list
        
    else :
        print ('section \'DRIVES\' not found in Config.ini')

    return drive_list


def get_doc_folder_name(config: object):

    """
    Get the document folder name from the configuration object.

    Args:
        config (object): The configuration object.

    Returns:
        str or None: The document folder name if found in the configuration, otherwise None.

    """
    
    docFolderName = None

    if 'SYSTEM' in config._sections or 'system' in config._sections :
        if 'DocumentPath' in config['SYSTEM'] :
            docFolderName = config['SYSTEM']['DocumentPath']
            print (docFolderName)

        else :
            print ("switch 'DocumentPath' not found in Config.ini")
        
    else :
        print ('section \'SYSTEM\' not found in Config.ini')

    return docFolderName


def split_by_string(text, split_string):
    import re
    
    res = []

    # Searching for <splitString> and splitting <text> into two parts
    while re.match(f'^(.*?){re.escape(split_string)}(.*)$', text):
        discard, part, text = re.split(f'({re.escape(split_string)})', text, maxsplit=1)
        res.append(part)

    # Appending the last text piece
    res.append(text)
    return res


articleWordCoordinates = None


def create_OCRxmlFile(CDF_XML_EXE: str, artFolderPath: str, export_dir: str, destFile: str, logger):


    """
    Create Word XML files from CDF files using an external tool and a custom WordXmlCreation class.

    Args:
        CDF_XML_EXE (str): Path to the CDF to XML conversion executable.
        artFolderPath (str): Path to the folder containing CDF files.
        export_dir (str): Path to the directory where Word XML files will be exported.
        destFile (str): Destination file name.
        logger: Logger object for logging messages.

    Returns:
        Tuple: A tuple containing the result status, error message, extracted article text,
               article line coordinates, and page count.

    Raises:
        subprocess.CalledProcessError: If an error occurs during the subprocess execution.

    Notes:
        - This function processes CDF files to create Word XML files using an external tool.
        - The WordXmlCreation class is used to further process the generated XML files.
        - The function also extracts text from OCR files and processes it for further use.

    """

    import glob
    import os
    import subprocess
    import shutil

    # import WordXmlCreation

    resultOCR = 0
    errorOCR = ""

    logger.info("    Extract block information...")
   
    
    
    cdfList = glob.glob(os.path.join(artFolderPath, "*.cdf"))

    if len(cdfList) == 0:
        resultOCR = 0
        errorOCR = "article inconsistent"
        return

    cdfFile = cdfList[0]
    tmpfilename = os.path.join(artFolderPath, "_cdfxml_p.tmp")
    logger.info(f"{CDF_XML_EXE} {cdfFile} {tmpfilename} -o{artFolderPath} '-OcrOnPic'")

    try:
        # cmd = f"{CDF_XML_EXE} {cdfFile} {tmpfilename} '-o' {artFolderPath} '-OcrOnPic'"
        cmd = f"{CDF_XML_EXE} {cdfFile} {tmpfilename} '-o' {artFolderPath} '-OcrOnPic'"

        logger.info(cmd)
        # os.system(cmd)
        output = subprocess.run([CDF_XML_EXE, cdfFile, tmpfilename, f"-o{artFolderPath}", "-OcrOnPic"], check=True, text=True, capture_output= True)
        logger.info(output)

    except subprocess.CalledProcessError as e:
        logger.exception(f"Error creating xml from cdf, cdf2xml crashed: {tmpfilename}")
        logger.exception(str(e))
        return
    # cdfxmlhandle = open(tmpfilename, 'r', encoding='unicode')
    # inhalt = cdfxmlhandle.read()
    # cdfxmlhandle.close()
    # pages = split_by_string(inhalt, "PageRef")

    logger.info("Calling python script for word xml creation")
    destWordFilePathWithoutExt = os.path.join(export_dir, destFile)

    word2xml = WordXmlCreation()
    global articleWordCoordinates

    pageCount, ocr_text, articleLineCoordinates  = word2xml.createWordXmlFromRgnOcrXml(tmpfilename, destWordFilePathWithoutExt, logger)
   
    # to get the text from ocr file
    ocr_data = extract_text_from_ocr_file(artFolderPath)
    article_txt = parse_ocr_data(ocr_data) 
    # to get the text and coordinates from ocr file    
    articleLineCoordinates = to_get_text_from_ocr_file(artFolderPath)


    # os.remove(tmpfilename)

    pageno = 0
    for pageno in range(1, pageCount+1):
        #page number starts with 1 here instead of zero
        wordfilename = os.path.join(export_dir, f"{destFile}_{pageno}.xml")

        if os.path.exists(wordfilename):
            destfilename = os.path.join(artFolderPath, f"000000_{pageno}.xml")
            logger.info(f"{wordfilename} to {destfilename}")
            try:
                shutil.copy2(wordfilename, destfilename)
            except Exception as e:
                logger.exception("Error copying word xml file to Document folder")
                logger.exception(str(e))

        pageno += 1

    resultOCR = 1

    return resultOCR, errorOCR, article_txt, articleLineCoordinates, pageCount


def trim_longer_source_pages(pages: str):


    """
    Trims a string of pages to include only the first three if there are more than three.

    Args:
        pages (str): A string of pages separated by commas.

    Returns:
        str: The modified string with an ellipsis (...) at the end if pages were trimmed.
    """

    # Split the string into individual pages
    page_list = pages.split(',')

    # Check if count is more than 3
    if len(page_list) > 3:
        pages = f"{page_list[0]},{page_list[1]},{page_list[2]}..."
    
    return pages


def ParseSourceXml2DrawOnPDF(strFolderPath: str, conf: dict, logger, dia_imges: list = [], kw_hits: str=''):

    """
    Parses source XML file to draw on a PDF.

    Args:
        strFolderPath (str): The path to the folder containing the XML file.
        conf (dict): Configuration dictionary.
        logger: The logger object for logging messages.
        dia_imges (list, optional): A list to store the paths of the created color_dia images. Defaults to [].
        kw_hits (str, optional): Keyword hits. Defaults to ''.

    Returns:
        list: A list of color_dia image paths.
    """

    from PIL import Image, ImageDraw, ImageOps
    import time
    
    from io import BytesIO
    # import io
    # import configparser
    # config = configparser.ConfigParser(strict=False)
    # config.read(newbase_ini)

    sourceFileFullPaths=[]
    sourceFileSubPaths =[]
    ResizeFactor=1
   

    file = 'infosfullpage.xml' #  CreateSourcePageInfo switch in newbase.ini should be enabled before clipping articles
    strXmlFilePath = os.path.join(strFolderPath, file)  
    logger.info (strXmlFilePath)      

    if os.path.exists(strXmlFilePath)==False:
        logger.info("infosfullpage.xml file not found, Please enable CreateSourcePageInfo switch in newbase.ini and re-clip the article to export !!!")
        return -1
    

    xmlDoc = etree.parse(strXmlFilePath)
    root = xmlDoc.getroot()
    page_nodes = root.findall(".//page")
    page_count = len(page_nodes)
    Regions = xmlDoc.xpath("/assembling/page/region[@file]")

    for rgn in Regions:
        src_paper_sub_path =rgn.attrib['file']
        drive_key =  rgn.attrib['drive']
        drivePath = conf['DRIVES'][drive_key]
        doc_folder_path = drivePath + conf['doc_folder_name']
        src_paper_path = doc_folder_path + src_paper_sub_path

        if src_paper_path not in sourceFileFullPaths:
            sourceFileFullPaths.append(src_paper_path)
            sourceFileSubPaths.append(src_paper_sub_path)
    
    i=-1
    for srcFullPath in sourceFileFullPaths:
        i +=1
        if i >= conf['MAX_DIA_LIMIT']: #only 3 dia should be created
            break

        if os.path.exists(srcFullPath)==False:
            logger.error(srcFullPath + "\nError: Above Source Paper JPG file not found, terminating")
            return -1
        img = Image.open(srcFullPath)
        diaImg = img.copy()

        # diaImg.thumbnail(conf['DiaJpgSize'], Image.ANTIALIAS)
        diaImg.thumbnail(conf['DiaJpgSize'], Image.LANCZOS) #Resampling.LANCZOS

        
        
        ResizeFactor = img.size[0]/diaImg.size[0]
        draw = ImageDraw.Draw(diaImg)

        for region in Regions :

            if region.attrib['file'] != sourceFileSubPaths[i]:
                continue

            drivePath = region.attrib['drive']
            filePath = drivePath + region.attrib['file']

            source = region.xpath('./src')[0]   

            x0= int( int(source.attrib['x0'])/ResizeFactor )
            x1= int( int(source.attrib['x1'])/ResizeFactor )
            y0= int( int(source.attrib['y0'])/ResizeFactor )
            y1= int( int(source.attrib['y1'])/ResizeFactor )

            cropImg = diaImg.crop(box=(x0, y0, x1, y1))
            # cropImg.show()
            cropImg = ImageOps.invert(cropImg)
            
            
            diaImg.paste(cropImg, (x0,y0))

            draw.rectangle(((x0, y0), (x1, y1)), outline="red", width=int(10/ResizeFactor) )

        color_dia_name = "color_dia_" + str(i+1) +".jpg"    
        strDiaJpgFilePath = os.path.join(strFolderPath, color_dia_name)
        diaImg.save(strDiaJpgFilePath, dpi=(300,300))
        dia_imges.append(strDiaJpgFilePath)
   

    return dia_imges


def check_and_create_dia_images(strFolderPath: str, conf: dict, logger, is_having_dia: bool, dia_imges: list = []):


    """
    Checks if color_dia images exist in the given folder path, and creates them if they don't exist.

    Args:
        strFolderPath (str): The path to the folder containing the images.
        conf (dict): Configuration dictionary.
        logger: The logger object for logging messages.
        is_having_dia (bool): Indicates if the folder already has color_dia images.
        dia_imges (list, optional): A list to store the paths of the created color_dia images. Defaults to [].

    Returns:
        list: A list of color_dia image paths.
    """

    from PIL import Image, ImageDraw, ImageOps
   
    sourceFileFullPaths=[]
    sourceFileSubPaths =[]
    ResizeFactor=1

    file = 'infosfullpage.xml' #  CreateSourcePageInfo switch in newbase.ini should be enabled before clipping articles
    strXmlFilePath = os.path.join(strFolderPath, file)  
    logger.info (strXmlFilePath)      

    if os.path.exists(strXmlFilePath)==False:
        logger.info("infosfullpage.xml file not found, Please enable CreateSourcePageInfo switch in newbase.ini and re-clip the article to export !!!")
        return -1
    
    xmlDoc = etree.parse(strXmlFilePath)
    root = xmlDoc.getroot()
    page_nodes = root.findall(".//page")
    page_count = len(page_nodes)
    Regions = xmlDoc.xpath("/assembling/page/region[@file]")

    for rgn in Regions:
        src_paper_sub_path =rgn.attrib['file']
        drive_key =  rgn.attrib['drive']
        drivePath = conf['DRIVES'][drive_key]
        doc_folder_path = drivePath + conf['doc_folder_name']
        src_paper_path = doc_folder_path + src_paper_sub_path

        if src_paper_path not in sourceFileFullPaths:
            sourceFileFullPaths.append(src_paper_path)
            sourceFileSubPaths.append(src_paper_sub_path)

    artFiles = os.listdir(strFolderPath)

    try:

        if is_having_dia==False:  # no dia case
            return []
        
        elif 'color_dia_1.jpg' not in  artFiles and is_having_dia: #two dia case or one dia or 3 dia, creating dia images

            i=-1

            color_dia_name = "Color_dia.jpg"
            strDiaJpgFilePath = os.path.join(strFolderPath, color_dia_name)
            dia_imges.append(strDiaJpgFilePath)

            sourceFileFullPaths = sourceFileFullPaths[1:]

            for srcFullPath in sourceFileFullPaths:
                i +=1
                if i >= conf['MAX_DIA_LIMIT']-1: #only 3 dia should be created, one dia is already present, here creating two dias
                    break

                if os.path.exists(srcFullPath)==False:
                    logger.error(srcFullPath + "\nError: Above Source Paper JPG file not found, terminating")
                    return -1
                img = Image.open(srcFullPath)
                diaImg = img.copy()

                # diaImg.thumbnail(conf['DiaJpgSize'], Image.ANTIALIAS)
                diaImg.thumbnail(conf['DiaJpgSize'], Image.LANCZOS) #Resampling.LANCZOS

                ResizeFactor = img.size[0]/diaImg.size[0]
                draw = ImageDraw.Draw(diaImg)

                for region in Regions :

                    if region.attrib['file'] in srcFullPath:
                    
                        source = region.xpath('./src')[0]   

                        x0= int( int(source.attrib['x0'])/ResizeFactor )
                        x1= int( int(source.attrib['x1'])/ResizeFactor )
                        y0= int( int(source.attrib['y0'])/ResizeFactor )
                        y1= int( int(source.attrib['y1'])/ResizeFactor )

                        cropImg = diaImg.crop(box=(x0, y0, x1, y1))
                        # cropImg.show()
                        cropImg = ImageOps.invert(cropImg)
                        
                        diaImg.paste(cropImg, (x0,y0))

                        draw.rectangle(((x0, y0), (x1, y1)), outline="red", width=int(10/ResizeFactor) )

                color_dia_name = "color_dia_" + str(i+1) +".jpg"    
                strDiaJpgFilePath = os.path.join(strFolderPath, color_dia_name)
                diaImg.save(strDiaJpgFilePath, dpi=(300,300))
                dia_imges.append(strDiaJpgFilePath)
    
        elif is_having_dia:   # getting dia images if present
            i=-1
            color_dia_name = "Color_dia.jpg"
            strDiaJpgFilePath = os.path.join(strFolderPath, color_dia_name)
            dia_imges.append(strDiaJpgFilePath)
            sourceFileFullPaths = sourceFileFullPaths[1:]

            for srcFullPath in sourceFileFullPaths:
                i +=1
                if i >= conf['MAX_DIA_LIMIT']-1: # one dia is already present, here getting two dias or one
                    break
                
                color_dia_name = "color_dia_" + str(i+1) +".jpg"    
                strDiaJpgFilePath = os.path.join(strFolderPath, color_dia_name)
                dia_imges.append(strDiaJpgFilePath)
   
        return dia_imges
    
    except Exception as err:
        print("Err: ", err)


def parse_asmbl_xml4image_list(strFolderPath: str, logger):


    """
    Parses an XML file containing image regions and returns a list of image paths and coordinates.

    Args:
        strFolderPath (str): The path to the folder containing the XML file and images.
        logger: The logger object for logging messages.

    Returns:
        Tuple[list, bool]: A tuple containing a list of image paths and coordinates, and a boolean indicating if a specific image is present.
    """

    ass_xml_img_list = []
    file = 'assembling.xml'
    assXmlFilePath = os.path.join(strFolderPath, file)  
    logger.info (assXmlFilePath)      

    if os.path.exists(assXmlFilePath)==False:
        logger.info("assembling.xml file not found, Please re-clip the article to properly to export !!!")
        return -1

    xmlDoc = etree.parse(assXmlFilePath)
    root = xmlDoc.getroot()
    Regions = xmlDoc.xpath("/assembling/page/region[@file]")
    
    is_having_dia = False

    for page in root.findall('page'):
        x_img_list = []
        for region in page.findall('region'):
            if region.attrib['file'] != 'color_dia.jpg':
                source = region.find('src')
                dest = region.find('dest')
                
                img_path = source.attrib['file']
                img_full_path = strFolderPath+img_path

                des_x0 = int(dest.attrib['x0'])
                des_x1 = int(dest.attrib['x1'])
                des_y0 = int(dest.attrib['y0'])
                des_y1 = int(dest.attrib['y1'])
                
                x_img_list.append(tuple((img_full_path, des_x0, des_y0, des_x1, des_y1)))

            elif region.attrib['file'] == 'color_dia.jpg':
                is_having_dia = True

        
        ass_xml_img_list.append(x_img_list)

    return ass_xml_img_list, is_having_dia


def get_pdf_content_coords(pdf_path: str, art_area_cords: str, page_number: int=-1):
        
    """
    Extracts text from a PDF file within specified coordinates.

    Args:
        pdf_path (str): The path to the PDF file.
        art_area_cords (str): The coordinates (rectangle) of the area to extract, in the format "x1 y1 x2 y2".
        page_number (int, optional): The page number to extract text from (1-indexed). Defaults to -1 (extract from all pages).

    Returns:
        list: A list of extracted text items.
    """
       
    import fitz

    input_doc = fitz.open(pdf_path)
    if input_doc:
        if page_number != -1: #to write in a particular page
            page = input_doc[page_number-1]
            extracted_text = []

            for page_num in range(input_doc.page_count):
                page = input_doc[page_num]
                text = page.get_text("words", clip=art_area_cords)
                # text = page.get_text("blocks", clip=art_area_cords)
                extracted_text.extend(text)

            return extracted_text
        
        else: #write in all pages
            extracted_text = []

            page_cnt = 0
            for page in input_doc:

                text_list =[]
                text = page.get_text("words", clip=art_area_cords)
                
                text_list.append(text)
                extracted_text.extend(text_list)
                page_cnt +=1
                
            return extracted_text
            

def extract_text_from_ocr_file(artFolderPath: str):

    """
    Extracts text from all .OCR files in the specified directory and concatenates the text.

    Args:
        artFolderPath (str): The path to the folder containing the .OCR files.

    Returns:
        str: The concatenated text from all .OCR files in the directory.
    """

    ocr_data = ''
    for file in os.listdir(artFolderPath):
        if file.endswith('.OCR') or file.endswith('.ocr'):
            file = os.path.join(artFolderPath,file)
            with open(file, 'r', encoding='cp1252', errors='ignore') as file:
                data = file.read()
            ocr_data += data
            
    return ocr_data


def parse_ocr_data(ocr_data: str):

    """
    Parses the OCR data to extract and format the article text.

    Args:
        ocr_data (str): The OCR data containing the article text.

    Returns:
        str: The parsed and formatted article text.
    """

    lines = ocr_data.split('\n')
    
    ocr_txt_list = []

    previous_type = None
    for line in lines:

        if line.startswith('TY>'):
            present_type = line[3:]
        elif line.startswith('RE>'):
            
                if previous_type!=present_type:
                    if previous_type == '72' and present_type=='8':
                        ocr_txt_list.append(line[3:])
                    elif previous_type == '8' and present_type == '72':
                        ocr_txt_list.append(line[3:])
                    elif previous_type == '66' and present_type=='2':
                        ocr_txt_list.append(line[3:])
                    elif previous_type == '2' and present_type == '66':
                        ocr_txt_list.append(line[3:])
                    else:
                        ocr_txt_list.append('\n')
                        ocr_txt_list.append(line[3:])
                    previous_type = present_type
                else:
                    ocr_txt_list.append(line[3:])   
            
    article_text = ''
    j = 1
    for text_list1 in range(len(ocr_txt_list)):   
        text = ocr_txt_list[text_list1] 

        if j<=len(ocr_txt_list): 
            if text.endswith('-') and j!= len(ocr_txt_list) and ocr_txt_list[j][0].isalpha() and ocr_txt_list[j][0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    
                    text3 = ocr_txt_list[j].split(' ')
                    article_text += text[0:-1] + text3[0]
                    string1 = ' '.join(text3[1:])
                    ocr_txt_list[j] = string1
                    if article_text[-1] == '-':
                        article_text = article_text[:-1]
                    else:
                        article_text += ' '

            elif text != '':
                article_text += text
                if text == '\n':
                    pass
                else:
                    article_text += ' '

        j += 1

    if article_text.startswith('\n'): 
        article_text= article_text[1:]
    
    return article_text


def to_get_text_from_ocr_file(folder_path):

    """Extracts text and coordinates from OCR files in a given folder.

    Args:
        folder_path (str): The path to the folder containing OCR files.

    Returns:
        list: A list of lists of tuples. Each inner list represents text and coordinates
              for a page, where each tuple contains (text, x1, y1, x2, y2).
    """

    import os
    ocr_data = ''
    article_txt_list = []
    for file in os.listdir(folder_path):
        if file.endswith('.OCR') or file.endswith('.ocr'):
            file =  os.path.join(folder_path, file)
            with open(file, 'r', encoding='cp1252', errors='ignore') as file:
                ocr_data = file.read()

            lines = ocr_data.split('\n')
            
            article_page_txt = []
            for line in lines:
                if line.startswith('RE>'):
                    txt = line[3:]
                elif line.startswith('IS>'):
                    coords = line[3:].split(' ')
                    coords1 = []
                    for i in coords:
                        if i.isnumeric():
                            coords1.append(int(i))
                    article_page_txt.append(tuple((txt, int(coords1[0]), int(coords1[1]), int(coords1[2]), int(coords1[3]))))

            article_txt_list.append(article_page_txt)

    return article_txt_list


def check_and_create_ocr_files(artFolderPath: str):

    """
    Checks for the presence of .OCR files corresponding to .TIF files in a directory.
    If any .TIF file does not have a corresponding .OCR file, creates an empty .OCR file.

    Args:
        artFolderPath (str): The path to the folder containing the .TIF and .OCR files.

    """
    
    # Sets to store base names of .TIF and .OCR files
    tif_files = []
    ocr_files = []

    # Iterate over the files in the directory once
    for file in os.listdir(artFolderPath):
        base_name, ext = os.path.splitext(file)
        if ext == '.TIF':
            tif_files.append(base_name)
        elif ext == '.OCR' or ext == '.ocr':
            ocr_files.append(base_name)
            print(base_name)

    # Create missing .OCR files
    for base_name in tif_files:
        if base_name not in ocr_files:
            ocr_file_path = os.path.join(artFolderPath, f"{base_name}.OCR")
            with open(ocr_file_path, "w") as fil:
                pass


def pdf_creation(dia_images: list, ass_xml_images: list, is_having_dia: bool, articleWordCoordinates: list, page_count: int, strFolderPath: str, exportPDFPath: str, logger, conf: dict, article_rec: object):

    """
    Create a new PDF by assembling images and text into a PDF document.

    Args:
        dia_images (list): List of paths to images representing dias.
        ass_xml_images (list): List of paths to images in ass xml format.
        is_having_dia (bool): Flag indicating if dias are present.
        articleWordCoordinates (list): List of word coordinates for each article.
        page_count (int): Total number of pages in the PDF.
        strFolderPath (str): Path to the folder containing the images and XML files.
        exportPDFPath (str): Path to save the new PDF.
        logger: Logger object for logging messages.
        conf (dict): Dictionary containing configuration parameters.
        article_rec (object): Object containing information about the article.

    Returns:
        None. The function saves the new PDF at `exportPDFPath`.

    This function creates a new PDF by assembling images and text. It uses the NB_PDF_Export module for PDF manipulation.
    """

    inputArticlePDF = os.path.join(strFolderPath, "ARTICLES.pdf")
    newArticlePDF = os.path.join(strFolderPath, "ARTICLES_NEW.pdf")

    art_area_coordinates = (20, 125, 596, 800)

    tif_images_list = []
    for file_path in os.listdir(strFolderPath):
        if file_path.endswith('.TIF'):
            img_file_path = os.path.join(strFolderPath,file_path)
            tif_images_list.append(img_file_path)

    start_time = time.time()

    pdf_exp = NB_PDF_Export.NbPDFExport_Fitz(conf) # creating blank pdf object first    

    #txt_coordinates_info = get_pdf_content_coords(inputArticlePDF, art_area_coordinates, page_number=-1)
   
    pdf_exp.add_tif_img(tif_images_list, tot_pages=page_count)

    pdf_exp.add_ass_xml_img_obj(ass_xml_images, tot_pages=page_count)

    # pdf_exp.insert_pdf_text_into_new_pdf(txt_coordinates_info, tot_pages=page_count)

    # pdf_exp.insert_xml_text_into_new_pdf(articleWordCoordinates, tot_pages=page_count)

    pdf_exp.insert_article_text_into_new_pdf(articleWordCoordinates, tot_pages=page_count)

    pdf_exp.draw_line(x0 = conf['top_horz_line']['x0'],
                          y0 = conf['top_horz_line']['y0'],
                          x1 = conf['top_horz_line']['x1'],
                          y1 = conf['top_horz_line']['y1'],
                          tot_pages=page_count
                          )


    pdf_exp.draw_line(x0 = conf['bottom_horz_line']['x0'],
                          y0 = conf['bottom_horz_line']['y0'],
                          x1 = conf['bottom_horz_line']['x1'],
                          y1 = conf['bottom_horz_line']['y1'],
                          tot_pages=page_count
                          )
    
    ### ---------------------- meta area --------------- ###
        
    pdf_exp.draw_blank_image_shape(x=conf['top_cover']['x'], y= conf['top_cover']['y'],
                             width=conf['top_cover']['width'], height=conf['top_cover']['height'],
                            opacity=1 , tot_pages = page_count                 
                             )
    
    src_x=conf["source_logo"]['x'] 
    src_y=conf["source_logo"]['y']
    src_width=conf['source_logo']['width']
    src_height=conf['source_logo']['height']

    # blank_jpg = f".\\blank_std.jpg"

    #pdf_exp.add_image(blank_jpg, x=src_x, y=src_y+10, width=src_width+300, height=src_height+14, tot_pages=page_count, aspect_ratio=False)
    
  
    source_logo_path = f"{conf['LOGO_DIR']}\\{article_rec.SourceName}.jpg"
    if os.path.exists(source_logo_path):
        pdf_exp.add_image(  image_path=source_logo_path, 
                            x =src_x, y=src_y, height= src_height, width=src_width,
                            tot_pages=page_count #for all page
                        )
        
    else:
        pdf_exp.draw_source_text_in_rect_new_pdf(  x =src_x, y=src_y, width=src_width, height= src_height,
                                    text=article_rec.SourceName,
                                    font_name=conf['source_text']["ext_fontname"], 
                                    font_size=conf['source_text']['font_size'], 
                                    font_file_path = conf['source_text']['font_file_path'],
                                    tot_pages=page_count
                                    )
        
    # for meta data
    
    for key in conf['meta_dict'].keys():

        if 'field' in key:
            if key == 'Red_field':
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= article_rec.Readers,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)
                
            elif key == "Date_field":
                date_field_value = ''
                if type(article_rec.SourceDate)==datetime.datetime:
                    date_field_value = article_rec.SourceDate.strftime('%d.%m.%Y')
                else:
                    date_field_value = article_rec.SourceDate
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= date_field_value,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)
                
            elif key == "Size_field":
                if type(article_rec.ArticleSize)==int:
                    size_field_value = str(article_rec.ArticleSize)+" "+ 'cm2'
                else:
                    size_field_value = article_rec.ArticleSize
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= size_field_value,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)
                
            elif key == "Page_field":
                trimmed_source_page = trim_longer_source_pages(article_rec.SourcePage)

                page_field_value = trimmed_source_page
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= page_field_value,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)
            elif key == "Ave_field":
                ave_field_value = '€ '+ article_rec.Rate
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= ave_field_value,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)
            elif key == "Publish_field":
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= article_rec.Publishing,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)

            elif key == "Circ_field":
                pdf_exp.draw_meta_text_in_rect_new_pdf(
                            x = conf["meta_dict"][key]['x'], 
                            y = conf["meta_dict"][key]['y'], 
                            height=conf["meta_dict"][key]['height'],
                            width=conf["meta_dict"][key]['width'], 
                            text= article_rec.Circulation,
                            font_name=conf["ext_fontname"], 
                            font_size=conf["meta_dict"][key]['font_size'],
                            font_file_path = conf['meta_font_file_path'],
                             tot_pages = page_count)

        else:
            pdf_exp.draw_meta_text_in_rect_new_pdf(

                                    x = conf["meta_dict"][key]['x'], 
                                    y = conf["meta_dict"][key]['y'], 
                                    height=conf["meta_dict"][key]['height'],
                                    width=conf["meta_dict"][key]['width'], 
                                    text=key,
                                    font_name=conf['ext_fontname'], 
                                    font_size=conf["meta_dict"][key]['font_size'],
                                    font_file_path = conf['meta_font_file_path'],
                                    tot_pages=page_count)
            
   
    copyright_logo_path = f"{conf['LOGO_DIR']}\\copyright.jpg"
    
    pdf_exp.add_copyright( image_path=copyright_logo_path, 
                           x = conf["copy_right"]['x0'], 
                           y = conf["copy_right"]['y0'], 
                           width=conf["copy_right"]['width'],
                           height=conf["copy_right"]['height'],
                           tot_pages = page_count
                            #for all page
                         )
    

    # pdf_exp.delete_existing_thumbnail(  page_number=0, 
    #                                     img_x=conf['existing_dia']['x'], 
    #                                     img_y=conf['existing_dia']['y'], 
    #                                     img_width=conf['existing_dia']['width'], 
    #                                     img_height=conf['existing_dia']['height']
    #                                 )
    
    #Thumbnail cover in case failed to delete existing thumbnail
    # pdf_exp.add_image(blank_jpg, x=conf['existing_dia']['x'], y=conf['existing_dia']['y'], 
    #                     width=conf['existing_dia']['width']+100, height=conf['existing_dia']['height'], tot_pages=page_count, aspect_ratio=False)


    if is_having_dia:
        pdf_exp.add_dias(dia_images=dia_images, gap=conf['dia_gap'])


    pdf_exp.save_pdf( outputPDF=exportPDFPath)
    
    shutil.copy(exportPDFPath, inputArticlePDF)
    logger.debug(f"Output pdf is: {exportPDFPath} from Input PDF was: {inputArticlePDF}")
   
    
    """ 
    if len(dia_imges) > 1:
            NB_PDF_Export.CreateMultiThumbExportPyPDF2(inputPDF= inputArticlePDF ,outputPDF=exportPDFPath, thumb_images=dia_imges, source_name= article_rec.SourceName, config=conf)
        
    else:
        shutil.copy(inputArticlePDF, exportPDFPath)
    """ 
    logger.info("\n--- %s seconds for Dia jpg out file creation and writing to PDF ---" % (time.time() - start_time)) 
    print((time.time() - start_time))                                                                                       
    #input("Press Enter to continue...")


    """ Regions = xmlDoc.xpath("/assembling/page/region[@file]")
    #Regions = doc.xpath("//region")
    for region in Regions:
        if region.attrib['file'] not in sourceFileSubPaths:
            srcFileSubPath = region.attrib['file']
            sourceFileSubPaths.append(srcFileSubPath)

            driveName = region.attrib['drive']
            drivePath = config['DRIVES'][driveName]
            driveWithDocFolder = os.path.join(drivePath, DocumentsFolder)
            # driveWithDocFolder = DrivesWithDocFolder[driveName]
         
            # srcFullPath = os.path.join(driveWithDocFolder, srcFileSubPath)
            srcFullPath = driveWithDocFolder + srcFileSubPath
            sourceFileFullPaths.append(srcFullPath) """


# def add_numbers(a, b):
#     return a + b

# def calculate_total():
#     return add_numbers(10, 20)




if __name__=='__main__':


    """
    This script processes articles based on certain conditions and exports them.
    It uses multiprocessing to parallelize the processing of articles.

    Usage:
        python script.py [-a] [-d] [-artls ART_LIST_STR]

    Options:
        -a, --auto       Run in automatic mode to process records of today.
        -d, --debug      Run in debug mode to print values instead of logging.
        -artls ART_LIST_STR
                        Run in manual export mode, processing selected records
                        provided in ART_LIST_STR.

    Requirements:
        - Setting module must define config_dict as conf.
        - DbOperation module must be imported for database operations.
        - utils module must be imported for utility functions.

    """


    import argparse
    from multiprocessing import Process, pool

    from Setting import config_dict as conf

    # from threading import Thread


    ## Include fulltext in the XML output?
    bFulltext = True

    DoHighlighting = False

    # package require NBPDFlib
    # nbpdflib::setNewbaseIni $NEWBASEINI
    
    e = datetime.datetime.now()
    print ("The time is now: = %s:%s:%s" % (e.hour, e.minute, e.second))

    if conf['EXPORT_DIR'] is not Empty:
        if not os.path.exists(conf['EXPORT_DIR']):
            try:
                os.mkdir(conf['EXPORT_DIR'])
            except Exception as err:
                print( "Error: export directory" + conf['EXPORT_DIR'] +" could not be created " + str(err) )
                exit()
    else:
        print("Error: no export directory choosen.")
        exit()
    
    config = configparser.ConfigParser(strict=False)
    config.read(conf['NEWBASEINI'])
    conf['DSN'] = getDSN(config)  

    
    conf['doc_folder_name'] = get_doc_folder_name(config)
    conf['drive_list'] = get_drive_list(config)
    conf['DRIVES']  = get_drive_dict(config)
    

    # conf['export_list'] = get_xml_meta_list(conf['ARTICLE_DES_PATH'])
    conf['export_list'] = parse_article_des_for_NoExpColumns (conf['ARTICLE_DES_PATH'])

    # rs [serachTable Articles sort=ChangeTime send<2 ICR=1]
    # rs [serachTable Articles sort=ChangeTime send=1 ICR=1]
    # rs [serachTable Articles send=0 ICR=1 ReICR=0]
    # rs = serachTable(tableName='Articles', sortBy='ChangeTime', condition='send<2 ICR=1' )
    today = datetime.datetime.today()
    today_date_str = today.strftime('%m.%d.%Y')

    # Initialize the parser
    parser = argparse.ArgumentParser(description='Please give the option to run in manual mode by taking art_list or Auto mode')

    # Add arguments
    parser.add_argument('-artls', '--art_list_str', type=str, help='for running in manual export mode, to process selected records given in cmdline')
    parser.add_argument('-a', '--auto', action='store_true'  ,help='for running in automatic mode to process record of today ')
    parser.add_argument('-d', '--debug', action='store_true'  ,help='for running in debug mode to print values instead of logging ')
    

    # Parse arguments
    args = parser.parse_args()

    DEBUG = args.debug

    db = DbOperation(conf['DSN'])

    if args.auto:
        start_time = time.time()
        # rs = db.search_table( tableName='Articles', condition=f"send=0 and ICR=1 and ChangeDate='{today_date_str}'", sortBy='changetime')
        rs = db.search_table( tableName='Articles', condition=f"send<3 and ICR=1 and ChangeDate='{today_date_str}'", sortBy='changetime')
        # rs = db.search_table( tableName='Articles', condition=f"send=20 and ICR=1 and ChangeDate='{today_date_str}'", sortBy='changetime')
        # rs = db.search_table( tableName='Articles', condition=f"send<20 and ICR=1", sortBy='changetime')
        print("No of Articles to process is: " + str(len(rs)))
        
        art_nos = [row[15] for row in rs]
        # print(art_nos)  # Output: ['John', 'Jane', 'Doe']


        exported_rs = db.search_table(tableName='Articles', condition=f"ExportInfo like '%MultiDia%' and ChangeDate='{today_date_str}' and send<20")
        
        already_exporeted_today = len(exported_rs)
        max_artilce_limit -= already_exporeted_today
        if max_artilce_limit <=0:
            print("Already {already_exporeted_today} Article Export Limit Exceeded.\nExported 0 Articles.")
            exit()

        
        db.columns_list['Articles'] = [column[0] for column in db.cursor.description]
        # print(rs)
        cpu_count = multiprocessing.cpu_count()
        
        max_time_limits = []
        active_processes = []
        process_list = []
        i = 0
        for rec in rs :
            print ("ArticleNo: " + str(rec.ArticleNo) + " SourceName: " + str(rec.SourceName) + " Send=" + str(rec.Send))
            
            if rec.ChangeTime:
                systemTime = datetime.datetime.now()
                
                strChangeTime = rec.ChangeTime
                #articleChangeTime = strChangeTime.strftime("%Y-%m-%d %H:%M:%S")
                articleBlockedTime = systemTime - rec.ChangeTime

                #strArticleBlockedTime = articleBlockedTime.strftime(r"%H:%M:%S")
                print("Article with article blocked time in seconds: " + str(articleBlockedTime.seconds) )
                
            # if rec.Volume:
            #     articleNo = getArticleNumber4mVolume(rec.Volume)
            #     getArticleFolderPath(rec.ArticleNo)
            source_pages = rec.SourcePage
            no_of_page = len(source_pages.split(','))
            print(f'No Of pages= {no_of_page}')
            max_time_limits.append(no_of_page*4) # since each article page export takes 4 sec average

            # Wait until the number of active processes is less than the maximum
            while len(active_processes) >= cpu_count or len(active_processes) >= max_process_limit:
                for process in active_processes:
                    if not process.is_alive():
                        print ('removing process id: ' + str(process.pid))
                        active_processes.remove(process)
                        break

            if i >= max_artilce_limit :
                break
            i += 1

            log_folder_path = os.path.join(conf['log_folder'], f"AutoExp_{today_date_str}")
            
            if os.path.exists(log_folder_path)==False:
                os.makedirs(log_folder_path)

            error_folder_path = os.path.join(log_folder_path, "Error")

            if os.path.exists(error_folder_path)==False:
                os.makedirs(error_folder_path)
            

            p = multiprocessing.Process(target=process_article, args=(rec, conf, db.columns_list, log_folder_path, error_folder_path, DEBUG), )
            # p = pool.apply_async(process_article, args=(rec, conf, db.columns_list, today_date_str,),)
        
            active_processes.append(p)
            process_list.append(p)

            p.start()

            # print(f"Active process count is {len(active_processes)}") # for debug
            
            if len(active_processes) >= (cpu_count):
                time.sleep(1) 

            # if i >= max_artilce_limit:
            #     break

            # i += 1 

        # # Wait for all worker processes to finish
        for p in process_list:
            p.join(max_time_limits[process_list.index(p)])



        # Create a multiprocessing pool
        # pool = multiprocessing.Pool(processes=cpu_count)

        print("No of Articles processed: " + str(i))
        print("time_taken: ",(time.time() - start_time))

    elif args.art_list_str: # e.g. "-artls", "25 26"

        start_time = time.time()
        art_list = args.art_list_str.split()
        art_tpl = tuple( art_list )

        log_folder_path = conf['log_folder']

        if os.path.exists(log_folder_path)==False:
            os.makedirs(log_folder_path)
        
        error_folder_path = os.path.join(log_folder_path, "Error")

        if os.path.exists(error_folder_path)==False:
            os.makedirs(error_folder_path)

        rs = db.search_table(tableName='Articles', condition=f"ArticleNo in {art_tpl}")
        
        db.columns_list['Articles'] = [column[0] for column in db.cursor.description]

        for rec in rs :
            process_article(rec, conf, db.columns_list, log_folder_path, error_folder_path)
        
        print("time_taken: ",(time.time() - start_time))

    
