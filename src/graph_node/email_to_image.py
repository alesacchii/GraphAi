from email import policy
from email.parser import BytesParser
from pathlib import Path

from html2image import Html2Image

from src.log_config import logger
from src.graph_config.state import EmailState


def email_to_image(state: EmailState) -> dict:
    logger.info("[NODE: email_to_image] Inizio conversione .eml -> immagine")
    eml_path = Path(state["file_path"])
    output_dir = Path("src/data/email_img/")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[NODE: email_to_image] Lettura del file email: {eml_path}")

    with eml_path.open("rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    html_part = msg.get_body(preferencelist=("html",))
    if html_part is not None:
        logger.info("[NODE: email_to_image] Trovata parte HTML nella email")
        full_html = html_part.get_content()
    else:
        logger.info("[NODE: email_to_image] Nessuna parte HTML, fallback su testo plain")
        text_part = msg.get_body(preferencelist=("plain",))
        text = text_part.get_content() if text_part else ""
        full_html = (
            f"<html><head><meta charset='utf-8'></head>"
            f"<body><pre style='font-family:monospace;white-space:pre-wrap;'>{text}</pre>"
            f"</body></html>"
        )

    output_name = f"{eml_path.stem}.png"
    hti = Html2Image(output_path=str(output_dir), size=(1200, 1600))
    hti.screenshot(html_str=full_html, save_as=output_name)
    output_path = str(output_dir / output_name)
    logger.info(f"[NODE: email_to_image] Immagine generata: {output_path}")

    return {"image_path": output_path}
