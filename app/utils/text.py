import re
from app.core.config import CHUNK_TARGET_MAX_CHARS, CHUNK_ABSOLUTE_MAX_CHARS


def preprocess_text_ptbr(text: str) -> str:
    """Pré-processamento de texto para pt-BR.
    Trata acentos, cedilha, caracteres especiais e converte
    abreviações/números para forma falada."""
    text = text.strip()

    # --- Caracteres Unicode especiais → equivalentes simples ---
    # Aspas tipográficas → aspas simples (evita artefatos no TTS)
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # " "
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')  # « »

    # Travessão e en-dash → vírgula ou pausa
    text = text.replace('\u2014', ', ')  # —
    text = text.replace('\u2013', ', ')  # –

    # Reticências tipográficas → três pontos
    text = text.replace('\u2026', '...')  # …

    # Espaços especiais → espaço normal
    text = re.sub(r'[\u00a0\u200b\u200c\u200d\u2060\ufeff]', ' ', text)

    # --- Limpeza básica ---
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remover caracteres que o TTS não consegue pronunciar
    text = re.sub(r'[#*_~`|<>{}[\]\\^]', '', text)

    # Pontuação repetida → única (evita artefatos)
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)

    # --- Abreviações pt-BR ---
    # Usa (?=\s|$|,) ao invés de \b no final, porque \b não funciona bem após ponto
    _end = r'(?=\s|$|,)'
    replacements = {
        r'\bDr\.' + _end: 'Doutor',
        r'\bDra\.' + _end: 'Doutora',
        r'\bSr\.' + _end: 'Senhor',
        r'\bSra\.' + _end: 'Senhora',
        r'\bSrta\.' + _end: 'Senhorita',
        r'\bProf\.' + _end: 'Professor',
        r'\bProfa\.' + _end: 'Professora',
        r'\bEng\.' + _end: 'Engenheiro',
        r'\bAdv\.' + _end: 'Advogado',
        r'\bAv\.' + _end: 'Avenida',
        r'\bn[°º\u00b0]' + _end: 'número',
        r'\bN[°º\u00b0]' + _end: 'Número',
        r'\betc\.' + _end: 'etcétera',
        r'\bp[áa]g\.' + _end: 'página',
        r'\bvol\.' + _end: 'volume',
        r'\bcap\.' + _end: 'capítulo',
        r'\bex\.' + _end: 'exemplo',
        r'\bobs\.' + _end: 'observação',
        r'\btel\.' + _end: 'telefone',
        r'\bdepto?\.' + _end: 'departamento',
        r'\bmin\.' + _end: 'minutos',
        r'\bseg\.' + _end: 'segundos',
        r'\bhr?s?\.' + _end: 'horas',
        r'\bjan\.' + _end: 'janeiro',
        r'\bfev\.' + _end: 'fevereiro',
        r'\bmar\.' + _end: 'março',
        r'\babr\.' + _end: 'abril',
        r'\bjun\.' + _end: 'junho',
        r'\bjul\.' + _end: 'julho',
        r'\bago\.' + _end: 'agosto',
        r'\bset\.' + _end: 'setembro',
        r'\bout\.' + _end: 'outubro',
        r'\bnov\.' + _end: 'novembro',
        r'\bdez\.' + _end: 'dezembro',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # --- Ordinais ---
    ordinals = {
        r'\b1[ºo]\b': 'primeiro',
        r'\b2[ºo]\b': 'segundo',
        r'\b3[ºo]\b': 'terceiro',
        r'\b4[ºo]\b': 'quarto',
        r'\b5[ºo]\b': 'quinto',
        r'\b6[ºo]\b': 'sexto',
        r'\b7[ºo]\b': 'sétimo',
        r'\b8[ºo]\b': 'oitavo',
        r'\b9[ºo]\b': 'nono',
        r'\b10[ºo]\b': 'décimo',
        r'\b1[ªa]\b': 'primeira',
        r'\b2[ªa]\b': 'segunda',
        r'\b3[ªa]\b': 'terceira',
        r'\b4[ªa]\b': 'quarta',
        r'\b5[ªa]\b': 'quinta',
        r'\b6[ªa]\b': 'sexta',
        r'\b7[ªa]\b': 'sétima',
        r'\b8[ªa]\b': 'oitava',
        r'\b9[ªa]\b': 'nona',
        r'\b10[ªa]\b': 'décima',
    }
    for pattern, replacement in ordinals.items():
        text = re.sub(pattern, replacement, text)

    # --- Moeda e porcentagem ---
    text = re.sub(r'R\$\s*(\d[\d.,]*)', _currency_to_text, text)
    # Remover "centavos" se já vier escrito após valor monetário
    text = re.sub(r'(centavos?)\s+centavos?', r'\1', text)
    text = re.sub(r'(\d[\d.,]*)\s*%', r'\1 por cento', text)

    # --- Horários (03:17 → três e dezessete) ---
    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', _time_to_text, text)

    # --- Números grandes ---
    text = re.sub(r'\b(\d{1,}(?:\.\d{3})*(?:,\d+)?)\b', _number_to_text, text)

    return text


# --- Conversores auxiliares ---

_UNITS = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
_TEENS = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
_TENS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
_HUNDREDS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']


def _int_to_text(n: int) -> str:
    """Converte inteiro (0-999999) para texto em pt-BR."""
    if n == 0:
        return 'zero'
    if n == 100:
        return 'cem'

    parts = []

    if n >= 1000:
        thousands = n // 1000
        n = n % 1000
        if thousands == 1:
            parts.append('mil')
        else:
            parts.append(f'{_int_to_text(thousands)} mil')

    if n >= 100:
        parts.append(_HUNDREDS[n // 100])
        n = n % 100

    if n >= 20:
        parts.append(_TENS[n // 10])
        n = n % 10

    if 10 <= n <= 19:
        parts.append(_TEENS[n - 10])
        n = 0

    if 1 <= n <= 9:
        parts.append(_UNITS[n])

    return ' e '.join(parts)


def _number_to_text(match: re.Match) -> str:
    """Converte números no texto para extenso."""
    num_str = match.group(1)
    # Número com separador de milhar (1.000) ou decimal (1,5)
    clean = num_str.replace('.', '').replace(',', '.')
    try:
        val = float(clean)
        if val > 999999:
            return num_str  # Números muito grandes ficam como estão
        if val == int(val):
            return _int_to_text(int(val))
        else:
            inteiro = int(val)
            decimal = num_str.split(',')[1] if ',' in num_str else ''
            if decimal:
                return f'{_int_to_text(inteiro)} vírgula {_int_to_text(int(decimal))}'
            return _int_to_text(inteiro)
    except (ValueError, IndexError):
        return num_str


def _currency_to_text(match: re.Match) -> str:
    """Converte R$ 1.500,00 → mil e quinhentos reais."""
    num_str = match.group(1)
    clean = num_str.replace('.', '').replace(',', '.')
    try:
        val = float(clean)
        inteiro = int(val)
        centavos = int(round((val - inteiro) * 100))

        parts = []
        if inteiro == 1:
            parts.append('um real')
        elif inteiro > 0:
            parts.append(f'{_int_to_text(inteiro)} reais')

        if centavos == 1:
            parts.append('um centavo')
        elif centavos > 0:
            parts.append(f'{_int_to_text(centavos)} centavos')

        if not parts:
            return 'zero reais'
        return ' e '.join(parts)
    except ValueError:
        return f'{num_str} reais'


def _time_to_text(match: re.Match) -> str:
    """Converte 03:17 → três e dezessete."""
    h = int(match.group(1))
    m = int(match.group(2))
    if m == 0:
        return f'{_int_to_text(h)} horas'
    return f'{_int_to_text(h)} e {_int_to_text(m)}'


def split_into_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?;:])\s+', text)
    sentences = []
    for part in parts:
        sub_parts = re.split(r'\n+', part)
        sentences.extend(s.strip() for s in sub_parts if s.strip())
    return sentences


def chunk_text(text: str) -> list[str]:
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(sentence) > CHUNK_ABSOLUTE_MAX_CHARS:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            sub_parts = re.split(r'(?<=,)\s+', sentence)
            sub_chunk = ""
            for sp in sub_parts:
                if len(sub_chunk) + len(sp) + 1 <= CHUNK_TARGET_MAX_CHARS:
                    sub_chunk = f"{sub_chunk} {sp}".strip() if sub_chunk else sp
                else:
                    if sub_chunk:
                        chunks.append(sub_chunk.strip())
                    sub_chunk = sp
            if sub_chunk:
                chunks.append(sub_chunk.strip())
            continue

        candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence

        if len(candidate) <= CHUNK_TARGET_MAX_CHARS:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
