import requests


class OpenHandsAPI:

    def __init__(
        self,
        api_key,
        base_url="https://app.all-hands.dev"
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # =========================================================
    # GENERIC REQUEST
    # =========================================================

    def _request(
        self,
        method,
        path,
        **kwargs
    ):

        url = f"{self.base_url}{path}"

        try:

            response = self.session.request(
                method,
                url,
                timeout=90,
                **kwargs
            )

        except requests.RequestException as error:

            raise RuntimeError(
                f"Network error:\n{error}"
            )

        if not response.ok:

            try:
                details = response.json()

            except Exception:
                details = response.text

            print(
                "\n"
                "================ API ERROR ================\n"
            )

            print(
                "METHOD:",
                method
            )

            print(
                "URL:",
                url
            )

            print(
                "STATUS:",
                response.status_code
            )

            print(
                "RESPONSE:",
                details
            )

            print(
                "============================================\n"
            )

            raise RuntimeError(
                f"HTTP {response.status_code}\n\n"
                f"URL:\n{url}\n\n"
                f"Response:\n{details}"
            )

        if not response.content:
            return {}

        try:

            return response.json()

        except Exception:

            return {
                "raw": response.text
            }

    # =========================================================
    # START CONVERSATION
    # =========================================================

    def start_conversation(
        self,
        repository,
        message
    ):

        data = {
            "initial_message": {
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            },
            "selected_repository": repository
        }

        return self._request(
            "POST",
            "/api/v1/app-conversations",
            json=data
        )

    # =========================================================
    # START TASK
    # =========================================================

    def get_start_task(
        self,
        task_id
    ):

        return self._request(
            "GET",
            "/api/v1/app-conversations/start-tasks",
            params={
                "ids": task_id
            }
        )

    # =========================================================
    # CONVERSATION
    # =========================================================

    def get_conversation(
        self,
        conversation_id
    ):

        return self._request(
            "GET",
            "/api/v1/app-conversations",
            params={
                "ids": conversation_id
            }
        )

    # =========================================================
    # SEND MESSAGE
    # =========================================================

    def send_message(
        self,
        conversation_id,
        message
    ):

        data = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        return self._request(
            "POST",
            f"/api/v1/app-conversations/"
            f"{conversation_id}/send-message",
            json=data
        )

    # =========================================================
    # SEARCH EVENTS
    # =========================================================

    def search_events(
        self,
        conversation_id,
        limit=100,
        page_start=None,
        max_pages=20
    ):

        all_items = []
        page_id = page_start
        last_offset = page_start or 0
        last_count = 0

        for _ in range(max_pages):

            params = {
                "limit": limit
            }

            if page_id:
                params["page_id"] = page_id

            result = self._request(
                "GET",
                f"/api/v1/conversation/"
                f"{conversation_id}/events/search",
                params=params
            )

            items = []

            if isinstance(result, dict):
                items = result.get("items", [])
            elif isinstance(result, list):
                items = result

            if not items:
                break

            all_items.extend(items)

            last_offset = page_id or 0
            last_count = len(items)

            if len(items) < limit:
                break

            page_id = (
                result.get("next_page_id")
                if isinstance(result, dict)
                else None
            )

            if page_id:

                try:
                    page_id = int(page_id)
                except (TypeError, ValueError):

                    page_id = None

            if not page_id:
                break

        cursor = None

        if all_items:

            try:
                cursor = (
                    int(last_offset or 0)
                    + int(last_count)
                )

            except (TypeError, ValueError):

                cursor = None

        return all_items, cursor

    # =========================================================
    # EVENT COUNT
    # =========================================================

    def count_events(
        self,
        conversation_id
    ):

        return self._request(
            "GET",
            f"/api/v1/conversation/"
            f"{conversation_id}/events/count"
        )

    # =========================================================
    # EVENT BATCH
    # =========================================================

    def get_events(
        self,
        conversation_id,
        event_ids
    ):

        data = {
            "event_ids": event_ids
        }

        return self._request(
            "GET",
            f"/api/v1/conversation/"
            f"{conversation_id}/events",
            json=data
        )

    # =========================================================
    # GIT CHANGES
    # =========================================================

    def get_git_changes(
        self,
        conversation_id
    ):

        return self._request(
            "GET",
            f"/api/v1/app-conversations/"
            f"{conversation_id}/git/changes"
        )

    # =========================================================
    # GIT DIFF
    # =========================================================

    def get_git_diff(
        self,
        conversation_id
    ):

        return self._request(
            "GET",
            f"/api/v1/app-conversations/"
            f"{conversation_id}/git/diff"
        )

    # =========================================================
    # CREDITS
    # =========================================================

    def get_credits(self):

        return self._request(
            "GET",
            "/api/billing/credits"
        )

    # =========================================================
    # CONVERSATION LIST
    # =========================================================

    def list_conversations(
        self,
        limit=50
    ):

        result = self._request(
            "GET",
            "/api/v1/app-conversations/search",
            params={
                "limit": limit
            }
        )

        if isinstance(result, dict):

            items = result.get(
                "items", result.get(
                    "conversations", []
                )
            )

        else:

            items = result

        return items or []

    # =========================================================
    # SUBSCRIPTION
    # =========================================================

    def get_subscription(self):

        return self._request(
            "GET",
            "/api/billing/subscription-access"
        )

    # =========================================================
    # MODELS
    # =========================================================

    def search_models(self):

        return self._request(
            "GET",
            "/api/v1/config/models/search"
        )

    # =========================================================
    # PROVIDERS
    # =========================================================

    def search_providers(self):

        return self._request(
            "GET",
            "/api/v1/config/providers/search"
        )

    # =========================================================
    # REPOSITORIES
    # =========================================================

    def search_repositories(
        self,
        search=""
    ):

        params = {}

        if search:
            params["search"] = search

        return self._request(
            "GET",
            "/api/v1/git/repositories/search",
            params=params
        )

    # =========================================================
    # USER
    # =========================================================

    def get_user(self):

        return self._request(
            "GET",
            "/api/v1/users/me"
        )