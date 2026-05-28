"""Email delivery channel via SMTP."""

import datetime
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses

from .base import Channel


class EmailChannel(Channel):
    """Send digest as an HTML email via SMTP.

    Precedence for each setting: config.yaml > environment variable > default.
    EMAIL_PASSWORD is environment-only — never read from config.yaml.

    Required (no default):
        EMAIL_USERNAME   SMTP login username (Gmail address)
        EMAIL_PASSWORD   SMTP password or app password (env-only)
        EMAIL_TO         Recipient address(es); comma-separated for
                         multiple recipients. Display names are allowed
                         (RFC 5322 — quoted "Last, First" forms with
                         embedded commas are parsed correctly).

    Optional:
        EMAIL_SMTP_HOST  SMTP server host (default: smtp.gmail.com)
        EMAIL_SMTP_PORT  SMTP port (default: 587 for STARTTLS)
        EMAIL_FROM       From address (default: EMAIL_USERNAME)
    """

    def __init__(self, config):
        self.smtp_host = (
            config.get("smtp_host")
            or os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
        )
        self.smtp_port = int(
            config.get("smtp_port")
            or os.environ.get("EMAIL_SMTP_PORT", "587")
        )
        self.username = config.get("username") or os.environ.get("EMAIL_USERNAME")
        self.password = os.environ.get("EMAIL_PASSWORD")
        self.from_addr = (
            config.get("from")
            or os.environ.get("EMAIL_FROM")
            or self.username
        )

        # Parse recipients: accept comma-separated list, with or without
        # display names (RFC 5322). `to_addrs` is the bare-address list passed
        # to SMTP RCPT TO; `to_addr_display` is the original string used in
        # the visible "To:" header so display names are preserved.
        raw_to = config.get("to") or os.environ.get("EMAIL_TO") or ""
        parsed = getaddresses([raw_to])
        self.to_addrs = [addr for _, addr in parsed if addr]
        self.to_addr_display = raw_to.strip()

        if not self.username or not self.password:
            raise RuntimeError(
                "EMAIL_USERNAME and EMAIL_PASSWORD must be set as environment variables.\n"
                "  Gmail: generate an App Password at myaccount.google.com/apppasswords\n"
                "  Then: export EMAIL_USERNAME=<your-address> EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx"
            )
        if not self.to_addrs:
            raise RuntimeError(
                "Recipient address not configured.\n"
                "  Set 'to' in config.yaml under channels.email, or set EMAIL_TO env var\n"
                "  (comma-separated for multiple recipients)."
            )

    @property
    def char_limit(self):
        return None  # no character limit for email

    def publish(self, header, papers):
        today = datetime.date.today().strftime("%Y-%m-%d")
        subject = f"📚 arXiv Digest {today} ({len(papers)} 件)"

        plain = self._format_plain(header, papers)
        html = self._format_html(header, papers, today)

        msg = MIMEMultipart("alternative")
        # Header() wraps non-ASCII subject as RFC 2047 (=?utf-8?b?...?=) so
        # all mail clients (Apple Mail / Outlook / Thunderbird / Gmail) render
        # it correctly instead of relying on raw-UTF-8 tolerance.
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr_display

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        self._send(msg)
        print(f"Email: sent digest with {len(papers)} papers to {self.to_addr_display}")

    # ------------------------------------------------------------------
    # Plain-text fallback
    # ------------------------------------------------------------------

    def _format_plain(self, header, papers):
        lines = [header, "=" * 60, ""]
        for p in papers:
            score = p.get("score", 0)
            title = p.get("title", "Untitled")
            url = p.get("url", "")
            authors = p.get("authors", [])
            cats = ", ".join(p.get("categories", [])[:3])
            reason = p.get("reason", "")
            summary = p.get("summary", "")

            author_str = self._author_str(authors)

            lines += [
                f"⭐ {score}/100 | {cats}",
                f"👤 {author_str}",
                f"📄 {title}",
                "",
            ]
            if reason:
                lines += [reason, ""]
            if summary:
                lines += [summary, ""]
            lines += [url, "-" * 40, ""]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # HTML body
    # ------------------------------------------------------------------

    def _format_html(self, header, papers, today):
        paper_html = "".join(self._paper_card(p) for p in papers)
        header_html = self._escape(header).replace("\n", "<br>")

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif;
             max-width:680px;margin:0 auto;padding:16px;color:#1a1a2e;background:#f5f5f5;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
              color:white;padding:20px 24px;border-radius:10px 10px 0 0;">
    <div style="font-size:1.5em;font-weight:700;">📚 arXiv Digest</div>
    <div style="margin-top:4px;opacity:0.7;font-size:0.9em;">{today}</div>
  </div>

  <!-- Summary bar -->
  <div style="background:#e8eaf6;padding:12px 24px;border-left:4px solid #3f51b5;
              font-size:0.92em;white-space:pre-wrap;">{header_html}</div>

  <!-- Papers -->
  <div style="padding:16px 0;">
    {paper_html}
  </div>

  <!-- Footer -->
  <div style="text-align:center;padding:16px;color:#888;font-size:0.8em;">
    Generated by <a href="https://github.com/odakin/arxiv-digest"
      style="color:#888;">arXiv-digest</a>
  </div>

</body>
</html>"""

    def _paper_card(self, paper):
        score = paper.get("score", 0)
        title = paper.get("title", "Untitled")
        url = paper.get("url", "")
        authors = paper.get("authors", [])
        cats = ", ".join(paper.get("categories", [])[:3])
        reason = paper.get("reason", "")
        summary = paper.get("summary", "")

        author_str = self._author_str(authors)

        # Score badge colour
        if score >= 93:
            badge_color = "#c0392b"
        elif score >= 85:
            badge_color = "#e67e22"
        else:
            badge_color = "#27ae60"

        reason_html = (
            f'<p style="margin:8px 0;line-height:1.6;">{self._escape(reason)}</p>'
            if reason
            else ""
        )
        summary_html = (
            f'<p style="margin:8px 0;color:#555;font-size:0.93em;line-height:1.6;">'
            f'{self._escape(summary)}</p>'
            if summary
            else ""
        )

        return f"""
    <div style="background:white;border-radius:8px;padding:16px 20px;
                margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,0.08);
                border-left:4px solid {badge_color};">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
        <span style="background:{badge_color};color:white;padding:2px 10px;
                     border-radius:12px;font-weight:700;font-size:0.9em;">⭐ {score}/100</span>
        <span style="color:#777;font-size:0.85em;">{self._escape(cats)}</span>
      </div>
      <div style="color:#666;font-size:0.88em;margin-bottom:4px;">👤 {self._escape(author_str)}</div>
      <div style="font-weight:600;font-size:1.02em;margin-bottom:8px;line-height:1.4;">
        <a href="{self._escape(url)}" style="color:#1a1a2e;text-decoration:none;">
          📄 {self._escape(title)}
        </a>
      </div>
      {reason_html}
      {summary_html}
      <div style="margin-top:10px;">
        <a href="{self._escape(url)}" style="color:#3f51b5;font-size:0.85em;word-break:break-all;">
          {self._escape(url)}
        </a>
      </div>
    </div>"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def post_text(self, text):
        """Send a plain-text notification (errors etc.)."""
        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = Header("arXiv Digest Notification", "utf-8")
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr_display
        self._send(msg)

    def _send(self, msg):
        """Send message via SMTP STARTTLS."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, self.to_addrs, msg.as_string())

    @staticmethod
    def _author_str(authors):
        last_names = []
        for a in authors:
            if ", " in a:
                last_names.append(a.split(", ")[0])
            else:
                parts = a.split()
                last_names.append(parts[-1] if parts else a)
        if len(last_names) > 4:
            return ", ".join(last_names[:4]) + " et al."
        return ", ".join(last_names)

    @staticmethod
    def _escape(text):
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
        )
