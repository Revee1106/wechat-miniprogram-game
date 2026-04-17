from __future__ import annotations

from pathlib import Path

from app.admin.repositories.enemy_config_repository import EnemyConfigRepository
from app.admin.repositories.event_config_repository import EventConfigRepository
from app.admin.schemas import EventDetailResponse, EventListResponse
from app.admin.services.event_validation_service import validate_event_config
from app.core_loop.types import NotFoundError


class EventAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = EventConfigRepository(base_path=self._base_path)
        self._enemy_repository = EnemyConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_events(
        self,
        event_type: str | None = None,
        risk_level: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        items = sorted(
            (
                template
                for template in payload["templates"]
                if self._matches_filters(
                    template,
                    event_type=event_type,
                    risk_level=risk_level,
                    keyword=keyword,
                )
            ),
            key=lambda template: (str(template.get("event_type", "")), str(template.get("event_id", ""))),
        )
        return {"items": items}

    def get_event(self, event_id: str) -> dict[str, object]:
        payload = self._repository.load()
        template = next(
            (item for item in payload["templates"] if item.get("event_id") == event_id),
            None,
        )
        if template is None:
            raise NotFoundError(f"event '{event_id}' not found")
        options = [
            option
            for option in payload["options"]
            if option.get("event_id") == event_id
        ]
        options.sort(key=lambda option: (int(option.get("sort_order", 1) or 1), str(option.get("option_id", ""))))
        response = EventDetailResponse(template=template, options=options)
        return {"template": response.template, "options": response.options}

    def create_event(self, template_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        if any(
            item.get("event_id") == template_payload.get("event_id")
            for item in payload["templates"]
        ):
            raise ValueError(f"event '{template_payload.get('event_id')}' already exists")
        payload["templates"].append(dict(template_payload))
        self._repository.save(payload)
        return dict(template_payload)

    def update_event(self, event_id: str, template_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        for index, template in enumerate(payload["templates"]):
            if template.get("event_id") == event_id:
                updated_template = dict(template_payload)
                updated_template["event_id"] = event_id
                payload["templates"][index] = updated_template
                self._repository.save(payload)
                return updated_template
        raise NotFoundError(f"event '{event_id}' not found")

    def delete_event(self, event_id: str) -> None:
        payload = self._repository.load()
        template_count_before = len(payload["templates"])
        payload["templates"] = [
            template for template in payload["templates"] if template.get("event_id") != event_id
        ]
        if len(payload["templates"]) == template_count_before:
            raise NotFoundError(f"event '{event_id}' not found")
        payload["options"] = [
            option for option in payload["options"] if option.get("event_id") != event_id
        ]
        self._repository.save(payload)

    def create_option(self, event_id: str, option_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        template = next(
            (item for item in payload["templates"] if item.get("event_id") == event_id),
            None,
        )
        if template is None:
            raise NotFoundError(f"event '{event_id}' not found")
        normalized_option = dict(option_payload)
        normalized_option["event_id"] = event_id
        option_id = str(normalized_option.get("option_id", "")).strip()
        if not option_id:
            option_id = self._build_next_option_id(
                event_id=event_id,
                options=payload["options"],
                sort_order=int(normalized_option.get("sort_order", 1) or 1),
            )
            normalized_option["option_id"] = option_id
        if any(item.get("option_id") == option_id for item in payload["options"]):
            raise ValueError(f"option '{option_id}' already exists")

        self._repair_blank_option_ref(
            template=template,
            option_id=option_id,
            sort_order=int(normalized_option.get("sort_order", 1) or 1),
        )
        repaired = self._repair_blank_option_record(
            payload=payload,
            template=template,
            event_id=event_id,
            normalized_option=normalized_option,
        )
        if not repaired:
            payload["options"].append(normalized_option)

        self._repository.save(payload)
        return normalized_option

    def update_option(self, option_id: str, option_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        for index, option in enumerate(payload["options"]):
            if option.get("option_id") == option_id:
                updated_option = dict(option_payload)
                updated_option["option_id"] = option_id
                payload["options"][index] = updated_option
                self._repository.save(payload)
                return updated_option
        raise NotFoundError(f"option '{option_id}' not found")

    def delete_option(self, option_id: str) -> None:
        payload = self._repository.load()
        option_count_before = len(payload["options"])
        payload["options"] = [
            option for option in payload["options"] if option.get("option_id") != option_id
        ]
        if len(payload["options"]) == option_count_before:
            raise NotFoundError(f"option '{option_id}' not found")
        for template in payload["templates"]:
            template["option_ids"] = [
                existing_option_id
                for existing_option_id in template.get("option_ids", [])
                if existing_option_id != option_id
            ]
        self._repository.save(payload)

    def validate_current_config(self):
        payload = self._repository.load()
        enemy_payload = self._enemy_repository.load()
        return validate_event_config(
            templates=payload["templates"],
            options=payload["options"],
            enemy_ids={
                str(enemy.get("enemy_id", "")).strip()
                for enemy in enemy_payload["items"]
                if str(enemy.get("enemy_id", "")).strip()
            },
        )

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        enemy_payload = self._enemy_repository.load()
        validation_result = validate_event_config(
            templates=payload["templates"],
            options=payload["options"],
            enemy_ids={
                str(enemy.get("enemy_id", "")).strip()
                for enemy in enemy_payload["items"]
                if str(enemy.get("enemy_id", "")).strip()
            },
        )
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid event config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_event_config(event_config_base_path=str(self._base_path))
        return {
            "reloaded": True,
            "template_count": len(payload["templates"]),
            "option_count": len(payload["options"]),
        }

    def _matches_filters(
        self,
        template: dict[str, object],
        *,
        event_type: str | None,
        risk_level: str | None,
        keyword: str | None,
    ) -> bool:
        if event_type and template.get("event_type") != event_type:
            return False
        if risk_level and template.get("risk_level") != risk_level:
            return False
        if keyword:
            haystack = " ".join(
                str(template.get(field, ""))
                for field in ("event_id", "event_name", "title_text", "body_text")
            ).lower()
            if keyword.lower() not in haystack:
                return False
        return True

    def _repair_blank_option_record(
        self,
        *,
        payload: dict[str, list[dict[str, object]]],
        template: dict[str, object],
        event_id: str,
        normalized_option: dict[str, object],
    ) -> bool:
        target_sort_order = int(normalized_option.get("sort_order", 1) or 1)

        for index, option in enumerate(payload["options"]):
            if option.get("event_id") != event_id:
                continue
            if str(option.get("option_id", "")).strip():
                continue
            if int(option.get("sort_order", 1) or 1) != target_sort_order:
                continue

            payload["options"][index] = normalized_option
            option_refs = list(template.get("option_ids", []))
            replaced = False
            for ref_index, option_ref in enumerate(option_refs):
                if not str(option_ref).strip():
                    option_refs[ref_index] = str(normalized_option["option_id"])
                    replaced = True
                    break
            if not replaced and str(normalized_option["option_id"]) not in option_refs:
                option_refs.append(str(normalized_option["option_id"]))
            template["option_ids"] = option_refs
            return True

        return False

    def _repair_blank_option_ref(
        self,
        *,
        template: dict[str, object],
        option_id: str,
        sort_order: int,
    ) -> None:
        option_refs = list(template.get("option_ids", []))
        if not option_refs or "" not in option_refs:
            return

        target_index = max(0, sort_order - 1)
        if target_index < len(option_refs) and not str(option_refs[target_index]).strip():
            option_refs[target_index] = option_id
            template["option_ids"] = option_refs
            return

        for index, option_ref in enumerate(option_refs):
            if not str(option_ref).strip():
                option_refs[index] = option_id
                template["option_ids"] = option_refs
                return

    def _build_next_option_id(
        self,
        *,
        event_id: str,
        options: list[dict[str, object]],
        sort_order: int,
    ) -> str:
        used_ids = {
            str(option.get("option_id", "")).strip()
            for option in options
            if str(option.get("event_id", "")) == event_id and str(option.get("option_id", "")).strip()
        }
        sequence = max(1, sort_order)

        while f"{event_id}_option_{sequence}" in used_ids:
            sequence += 1

        return f"{event_id}_option_{sequence}"
