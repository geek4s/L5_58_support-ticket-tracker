"""A small in-memory support ticket tracker.

Tickets are held in a module-level dictionary and can be created, assigned,
searched, updated and persisted to a JSON file on disk.
"""

import json
import logging
import os
from dataclasses import dataclass

TICKETS = {}


@dataclass
class TicketRequest:
    """The details needed to open a new support ticket."""

    title: str
    description: str
    reporter: str
    priority: str = "medium"
    category: str = "general"


def create_ticket(request, audit_log=None):
    """Create a ticket from *request* and record it in TICKETS.

    Returns the new ticket, or None when the request has no title.
    """
    if not request.title:
        return None
    if audit_log is None:
        audit_log = []
    ticket_id = str(len(TICKETS) + 1)
    ticket = {
        "id": ticket_id,
        "title": request.title,
        "description": request.description,
        "priority": request.priority,
        "category": request.category,
        "status": "open",
        "reporter": request.reporter,
        "assignee": None,
    }
    TICKETS[ticket_id] = ticket
    audit_log.append(f"Created ticket {ticket_id} for {request.reporter}")
    return ticket


def assign_ticket(ticket_id, agent):
    """Assign *ticket_id* to *agent*. Returns True on success."""
    try:
        TICKETS[ticket_id]["assignee"] = agent
        return True
    except KeyError:
        logging.warning("Cannot assign: no ticket with id %s", ticket_id)
    return False


def update_status(ticket_id, status):
    """Set the status of *ticket_id*. Returns the ticket, or None."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        logging.warning("Cannot update: no ticket with id %s", ticket_id)
        return None
    ticket["status"] = status
    return ticket


def search_tickets(status=None, priority=None):
    """Return the tickets matching the given status and/or priority."""
    results = []
    for ticket in TICKETS.values():
        if status is not None and ticket["status"] != status:
            continue
        if priority is not None and ticket["priority"] != priority:
            continue
        results.append(ticket)
    return results


def save_tickets(path="tickets.json"):
    """Write all tickets to *path* as JSON."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(TICKETS, handle)


def load_tickets(path="tickets.json"):
    """Replace the in-memory tickets with the contents of *path*."""
    with open(path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    TICKETS.clear()
    TICKETS.update(loaded)


def print_ticket_report():
    """Print a one-line summary of every ticket."""
    print("Support Tickets")
    if not TICKETS:
        print("No tickets yet")
    for ticket_id, ticket in TICKETS.items():
        print(ticket_id, ticket["title"], ticket["status"])


def close_ticket(ticket_id):
    """Mark *ticket_id* as closed."""
    return update_status(ticket_id, "closed")


def is_open(ticket_id):
    """Return True if *ticket_id* is still being worked on."""
    ticket = TICKETS.get(ticket_id)
    return ticket is not None and ticket["status"] in ("open", "in_progress")


def main():
    """Run a short demonstration of the tracker."""
    logging.basicConfig(level=logging.INFO)
    create_ticket(TicketRequest("Cannot sign in", "Password reset link fails", "alex@example.com"))
    create_ticket(TicketRequest("Billing question", "Charged twice", "lee@example.com", priority="high"))
    assign_ticket("1", "agent-01")
    update_status("1", "in_progress")
    print_ticket_report()
    logging.info("Tickets created: %s", len(TICKETS))
    print("Ticket 1 open?", is_open("1"))
    ticket_id = input("Ticket id to close (Enter to skip): ")
    if ticket_id:
        close_ticket(ticket_id)
    save_tickets()
    if os.environ.get("RUN_UNSAFE_DEMO") == "1":
        print("demo mode")


if __name__ == "__main__":
    main()
