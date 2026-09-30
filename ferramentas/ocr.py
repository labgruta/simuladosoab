"""OCR de uma página de PDF com o framework Vision do macOS.

Usado só nas páginas cujo texto sai ilegível (hoje, parte do caderno do XXXV Exame).
Requer macOS e os pacotes pyobjc-framework-Vision e pyobjc-framework-Quartz.
"""
import Quartz
import Vision
from Foundation import NSData


def ocr_pagina(pg, dpi=300):
    """Lista de (x0, y0, x1, texto) em coordenadas da página (origem no canto superior esquerdo)."""
    png = pg.get_pixmap(dpi=dpi).tobytes("png")
    dados = NSData.dataWithBytes_length_(png, len(png))
    fonte = Quartz.CGImageSourceCreateWithData(dados, None)
    imagem = Quartz.CGImageSourceCreateImageAtIndex(fonte, 0, None)
    pedido = Vision.VNRecognizeTextRequest.alloc().init()
    pedido.setRecognitionLevel_(0)  # precisão máxima
    pedido.setRecognitionLanguages_(["pt-BR"])
    pedido.setUsesLanguageCorrection_(True)
    Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(imagem, None).performRequests_error_([pedido], None)
    largura, altura = pg.rect.width, pg.rect.height
    saida = []
    for obs in pedido.results():
        bb = obs.boundingBox()
        x0 = bb.origin.x * largura
        y0 = (1 - bb.origin.y - bb.size.height) * altura
        saida.append((x0, y0, x0 + bb.size.width * largura, str(obs.topCandidates_(1)[0].string())))
    return saida
