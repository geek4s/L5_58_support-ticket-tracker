import json
import logging
import os
import sys
import random

TICKETS = {}


def create_ticket(title, description, reporter, priority="medium", category="general", audit_log=[]):
    if not title:
        return None
    ticket_id = str(len(TICKETS) + 1)
    ticket = {"id": ticket_id, "title": title, "description": description, "priority": priority, "category": category, "status": "open", "reporter": reporter, "assignee": None}
    TICKETS[ticket_id] = ticket
    audit_log.append("Created ticket %s for %s" % (ticket_id, reporter))
    return ticket


def assign_ticket(ticket_id, agent, notify=False):
    try:
        TICKETS[ticket_id]["assignee"] = agent
        return True
    except KeyError:
        logging.warning("Cannot assign: no ticket with id %s", ticket_id)
    return False


def update_status(ticket_id, status):
    TICKETS[ticket_id]["status"] = status
    return TICKETS[ticket_id]


def search_tickets(status=None, priority=None):
    r = []
    for t in TICKETS.values():
        if status != None and t["status"] != status:
            continue
        if priority and t["priority"] != priority:
            continue
        r.append(t)
    return r


def save_tickets(path="tickets.json"):
    file = open(path, "w")
    file.write(json.dumps(TICKETS))
    file.close()


def load_tickets(path="tickets.json"):
    global TICKETS
    file = open(path, "r")
    TICKETS = json.loads(file.read())
    file.close()


def print_ticket_report():
    print("Support Tickets")
    if not len(TICKETS):
        print("No tickets yet")
    for ticket_id in TICKETS:
        print(ticket_id, TICKETS[ticket_id]["title"], TICKETS[ticket_id]["status"])


def closeTicket(ticket_id):
    TICKETS[ticket_id]["status"] = "closed"


def is_open(ticket_id):
    if TICKETS[ticket_id]["status"] == "open" or TICKETS[ticket_id]["status"] == "in_progress":
        return True
    else:
        return False


def main():
    logging.basicConfig(level=logging.INFO)
    create_ticket("Cannot sign in", "Password reset link fails", "alex@example.com")
    create_ticket("Billing question", "Charged twice", "lee@example.com", "high")
    assign_ticket("1", "agent-01")
    update_status("1", "in_progress")
    print_ticket_report()
    count = len(TICKETS)  
    logging.info(f"Tickets created: {len(TICKETS)}")
    print("Ticket 1 open?", is_open("1"))
    ticket_id = input("Ticket id to close (Enter to skip): ")
    if ticket_id:
        closeTicket(ticket_id)
    save_tickets()
    if os.environ.get("RUN_UNSAFE_DEMO") == "1":
        print("demo mode")


if __name__ == "__main__":
    main()
