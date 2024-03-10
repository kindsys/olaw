import os
import requests
import re

from . import SearchTarget


class OpenLaws(SearchTarget):

    # TODO: see if any of the other OpenLaws response fields would be useful. This is the minimal set.
    RESULTS_DATA_FORMAT = {
        "openlaws_url": "", # OpenLaws URL for the law text.
        "source_url": "", # URL for the source of the law text.
        "name": "", # Name of the division.
        "path": "", # Hierarchical path of the division within the law.
        "text": "",  # Plaintext of the law.
        "prompt_text": "",  # Line of text used as part of the RAG prompt to introduce sources.
        "ui_text": "",  # Line of text used as part of the UI to introduce this source.
        "ui_url": "",  # URL used to let users explore this source.
    }
    """
    Shape of the data for each individual entry of search_results.
    """

    @staticmethod
    def search(search_statement: str):
        """
        Runs search_statement against the CourtListener search API.
        - Returns only 1 result.
        - Objects in list use the OpenLaws.RESULTS_DATA_FORMAT template.
        """
        api_url = os.environ["OPENLAWS_API_URL"]
        api_key = os.environ["OPENLAWS_API_KEY"]
        slim_len = int(os.environ.get("OPENLAWS_SLIM_LEN", "360"))

        prepared_results = []
        jurisdiction, citation = search_statement.split("|")
        
        # Clean/Validate Jurisdiction
        # TODO: improve
        jurisdiction = jurisdiction.strip().upper()
        fed_aliases = re.compile(r"^(US|FED)")
        if fed_aliases.match(jurisdiction):
            jurisdiction = "FED" 
        
        # Clean/Sanity Check Citation
        # TODO: improve
        citation = citation.strip()

        # Call OpenLaws API
        query_params = {"query": citation}
        url = f"{api_url}/jurisdictions/{jurisdiction}/citations"
        response = requests.get(
            url,
            timeout=30,
            params=query_params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        
        # Quit if not good status.
        if response.status_code >= 400:
            return prepared_results
        
        # Assuming success and relying on error to be thrown for now.
        division_json = response.json()
        idx = 0
        data = dict(OpenLaws.RESULTS_DATA_FORMAT)
        data["name"] = division_json["name"]
        data["openlaws_url"] = division_json["url"]
        data["path"]  = division_json["path"]
        data["source_url"] = division_json["source_url"]
        data["text"] = division_json["plaintext_content"]
        source_url = data["source_url"]

        # Prompt Text:
        # [1] 12 CFR § 1002.1 is as follows:
        # {law_text}
        # Source: {source_url}
        prompt_text = f"[{idx+1}] {citation} is as follows:\n"
        prompt_text += data["text"]
        prompt_text += f"\nSource: {source_url}\n\n"
        
        # UI Text (single-line format)
        # [1] 12 CFR § 1002.1 - {first n characters of law text}
        slim_law_text = data["text"][:slim_len]
        if len(data["text"]) > slim_len:
            slim_law_text = f"{slim_law_text.rstrip()}..."

        ui_text = f"[{idx+1}] {citation} - {slim_law_text}"
        
        data["prompt_text"] = prompt_text
        data["ui_text"] = ui_text
        # NOTE: could also use openlaws_url for a more consistent experience, but those links currently require auth so
        # currently we will use the source_url for the UI links.
        data["ui_url"] = data["source_url"]

        prepared_results.append(data)

        return prepared_results
