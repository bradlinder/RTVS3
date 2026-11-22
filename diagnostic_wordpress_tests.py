"""Diagnostic tests for WordPress PublishPress Author mapping and update semantics."""
from __future__ import annotations

from diagnostic_helpers import DiagnosticItem


class DiagnosticWordPressTestsMixin:
    """Mixin for WordPress & PublishPress Author mapping regression diagnostics."""

    def _test_wordpress_publishpress_author_mapping_and_update_semantics(self, item: DiagnosticItem):
        from plugins.wordpress.authors import (
            count_selected_authors,
            expand_legacy_author_term_ids,
            extract_checked_author_ids,
            is_author_item_selected,
            resolve_selected_author_names,
        )
        from plugins.wordpress.client import WordPressClient

        brad_user = {
            "id": 7, "term_id": 412, "user_id": 7, "name": "Brad Linder",
            "slug": "brad", "type": "PublishPress Author", "is_guest": False,
        }
        cohost_user = {
            "id": 12, "term_id": 418, "user_id": 12, "name": "Co-Host",
            "slug": "cohost", "type": "PublishPress Author", "is_guest": False,
        }
        guest_author = {
            "id": 519, "term_id": 519, "user_id": 0, "name": "Iffy Guest",
            "slug": "iffy-guest", "type": "Guest Author", "is_guest": True,
        }
        legacy_wp_user = {
            "id": 9, "term_id": None, "user_id": 9, "name": "Plain WP User",
            "slug": "plain-wp", "type": "WP User", "is_guest": False,
        }
        cached = [brad_user, cohost_user, guest_author]

        # 1. Mapped WP User + Guest Author: both term_ids included, guest excluded from author_ids
        a_ids, t_ids = extract_checked_author_ids([brad_user, guest_author])
        assert a_ids == [7], f"Expected [7], got {a_ids}"
        assert t_ids == [412, 519], f"Expected [412, 519], got {t_ids}"
        assert count_selected_authors(a_ids, t_ids) == 2

        # 2. Two mapped WP Users: both term_ids captured, count == 2
        a2, t2 = extract_checked_author_ids([brad_user, cohost_user])
        assert a2 == [7, 12] and t2 == [412, 418]
        assert count_selected_authors(a2, t2) == 2

        # 3. Fetching Guest-Only post (core author=7, ppma_author=[519]) must NOT check Brad
        assert is_author_item_selected(guest_author, [7], [519]) is True
        assert is_author_item_selected(brad_user, [7], [519]) is False
        assert resolve_selected_author_names(cached, [7], [519]) == ["Iffy Guest"]

        # 4. Fetching 2-WP-User post (core author=7, ppma_author=[412, 418]) checks BOTH users
        assert is_author_item_selected(brad_user, [7], [412, 418]) is True
        assert is_author_item_selected(cohost_user, [7], [412, 418]) is True
        assert resolve_selected_author_names(cached, [7], [412, 418]) == ["Brad Linder", "Co-Host"]

        # 5. Standard WP site without PublishPress terms (term_id=None)
        a_std, t_std = extract_checked_author_ids([legacy_wp_user])
        assert a_std == [9] and t_std == []
        assert is_author_item_selected(legacy_wp_user, [9], []) is True

        # 6. Legacy .rtvs project saved with author_ids=[7] only expands term_ids when PublishPress cache exists
        exp_a, exp_t = expand_legacy_author_term_ids([7], [], cached)
        assert exp_a == [7] and exp_t == [412], f"Expected [412], got {exp_t}"
        exp_std_a, exp_std_t = expand_legacy_author_term_ids([9], [], [legacy_wp_user])
        assert exp_std_a == [9] and exp_std_t == []

        # 7. WordPressClient.update_post payload invariants across overwrite & preserve cases
        captured_payloads = []

        class _FakeResp:
            status_code = 200
            text = "{}"

            def json(self):
                return {"id": 99}

        client = WordPressClient("https://example.com", "user", "pass")

        def _fake_post(_url, json_data=None, **_kw):
            captured_payloads.append(dict(json_data or {}))
            return _FakeResp()

        client._post_request = _fake_post

        # Mapped WP User + Guest -> sends both core author & full ppma_author list
        client.update_post(99, title="T", author_ids=[7], author_term_ids=[412, 519])
        assert captured_payloads[-1].get("author") == 7
        assert captured_payloads[-1].get("ppma_author") == [412, 519]

        # Mapped WP User ONLY (overwriting to remove Guest) -> sends ppma_author=[412]
        client.update_post(99, title="T", author_ids=[7], author_term_ids=[412])
        assert captured_payloads[-1].get("author") == 7
        assert captured_payloads[-1].get("ppma_author") == [412]

        # Guest ONLY -> omits core author, sends ppma_author=[519]
        client.update_post(99, title="T", author_ids=[], author_term_ids=[519])
        assert "author" not in captured_payloads[-1]
        assert captured_payloads[-1].get("ppma_author") == [519]

        # Empty selection -> omits both so WP preserves existing authors
        client.update_post(99, title="T", author_ids=[], author_term_ids=[])
        assert "author" not in captured_payloads[-1]
        assert "ppma_author" not in captured_payloads[-1]

        item.status = "PASS"
        item.message = "PublishPress User + Guest term_id extraction, fetch selection, and overwrite payloads verified"
