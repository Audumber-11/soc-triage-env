"""Sample data for IT Support environment - tickets, KB articles, and system components."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from .models import Ticket, TicketPriority, TicketStatus, KnowledgeBaseEntry, SystemComponent


# Sample tickets by difficulty level
EASY_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "TKT-001",
        "title": "Password Reset Request",
        "description": "User forgot their password and cannot log into their account. Username: jsmith. No suspicious activity detected.",
        "category": "access",
        "priority": TicketPriority.MEDIUM,
        "requester": "jsmith@company.com",
        "required_fixes": {"reset_password", "notify_user"},
    },
    {
        "id": "TKT-002",
        "title": "VPN Access Request",
        "description": "New employee needs VPN access to work remotely. Employee ID: E12345, Department: Engineering.",
        "category": "access",
        "priority": TicketPriority.HIGH,
        "requester": "hiring-manager@company.com",
        "required_fixes": {"provision_vpn", "send_credentials"},
    },
    {
        "id": "TKT-003",
        "title": "Printer Not Responding",
        "description": "HP LaserJet 4050 on floor 3 is not responding to print jobs. Status light shows offline.",
        "category": "hardware",
        "priority": TicketPriority.LOW,
        "requester": "floor3-admin@company.com",
        "required_fixes": {"check_printer_status", "restart_print_spooler"},
    },
    {
        "id": "TKT-004",
        "title": "Email Not Syncing on Mobile",
        "description": "User's company email not syncing on iPhone. Other apps working fine. Tried restart.",
        "category": "software",
        "priority": TicketPriority.MEDIUM,
        "requester": "mlopez@company.com",
        "required_fixes": {"check_email_settings", "reconfigure_exchange"},
    },
    {
        "id": "TKT-005",
        "title": "Monitor Display Issue",
        "description": "Dual monitor setup - second monitor showing 'No Signal'. Cable appears connected properly.",
        "category": "hardware",
        "priority": TicketPriority.LOW,
        "requester": "tchen@company.com",
        "required_fixes": {"check_display_settings", "verify_cable_connection"},
    },
]

MEDIUM_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "TKT-101",
        "title": "Intermittent Network Connectivity",
        "description": "User reports network drops every 15-20 minutes for past 2 days. Other users on same switch unaffected. Windows 11, Dell laptop. Event log shows 'Network adapter reset'.",
        "category": "network",
        "priority": TicketPriority.HIGH,
        "requester": "rwilliams@company.com",
        "required_fixes": {"check_network_adapter", "update_drivers", "test_cable", "verify_switch_port"},
    },
    {
        "id": "TKT-102",
        "title": "Database Connection Timeout",
        "description": "Application reports 'Connection timeout' when accessing CRM database. Issue started after weekend maintenance. Other databases accessible.",
        "category": "software",
        "priority": TicketPriority.CRITICAL,
        "requester": "crm-app@company.com",
        "required_fixes": {"check_db_status", "verify_connection_string", "check_firewall_rules", "restart_db_service"},
    },
    {
        "id": "TKT-103",
        "title": "Shared Drive Access Denied",
        "description": "User cannot access \\fileserver\shared\finance despite having permissions. Error: 'Access denied'. Worked yesterday.",
        "category": "access",
        "priority": TicketPriority.HIGH,
        "requester": "ajohnson@company.com",
        "required_fixes": {"verify_permissions", "check_ad_group", "test_path", "reset_kerberos_ticket"},
    },
    {
        "id": "TKT-104",
        "title": "Application Crash on Startup",
        "description": "Adobe Creative Suite crashes immediately on launch. Error code 0xC0000005. Reinstall attempted, issue persists.",
        "category": "software",
        "priority": TicketPriority.MEDIUM,
        "requester": "design-team@company.com",
        "required_fixes": {"check_system_requirements", "update_graphics_drivers", "check_corrupted_prefs", "disable_plugins"},
    },
    {
        "id": "TKT-105",
        "title": "SSL Certificate Error",
        "description": "Users getting certificate warning on internal company portal. Certificate shows expired yesterday. 50+ users affected.",
        "category": "network",
        "priority": TicketPriority.CRITICAL,
        "requester": "security-team@company.com",
        "required_fixes": {"verify_cert_expiry", "check_cert_manager", "renew_certificate", "update_bindings"},
    },
]

HARD_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "TKT-201",
        "title": "Multi-Site Replication Failure",
        "description": "Data replication between HQ and branch offices failing since 3 AM. Primary site operational, 4 branch sites not receiving updates. Error log shows 'Replication partner not found'. WAN links appear up. DFS Replication event 5008.",
        "category": "network",
        "priority": TicketPriority.CRITICAL,
        "requester": "ops-team@company.com",
        "required_fixes": {
            "check_dfs_health", "verify_wan_connectivity", "check_dns_resolution",
            "examine_replication_schedule", "check_firewall_ports", "verify_service_accounts",
            "analyze_event_logs", "test_site_connectivity"
        },
    },
    {
        "id": "TKT-202",
        "title": "Authentication Service Degradation",
        "description": "Intermittent login failures across multiple services. LDAP queries timing out. Affecting SSO, VPN, and internal apps. Pattern suggests AD controller issue. Some users can log in, others cannot.",
        "category": "access",
        "priority": TicketPriority.CRITICAL,
        "requester": "security-team@company.com",
        "required_fixes": {
            "check_ad_health", "verify_ldap_connectivity", "check_dns_replication",
            "examine_gc_availability", "check_ldap_query_limits", "review_security_logs",
            "test_auth_paths", "check_service_status"
        },
    },
    {
        "id": "TKT-203",
        "title": "Storage Array Performance Degradation",
        "description": "SAN showing 95th percentile latency >100ms (normal <10ms). No hardware failures reported. Performance impact on VMs. Cache hit rate dropped from 85% to 45%. Occurring across all LUNs.",
        "category": "hardware",
        "priority": TicketPriority.CRITICAL,
        "requester": "storage-admin@company.com",
        "required_fixes": {
            "check_cache_status", "analyze_io_patterns", "verify_controller_health",
            "check_disk_group_status", "review_rebuild_operations", "check_network_paths",
            "examine_queue_depths", "verify_snapshot_impact"
        },
    },
    {
        "id": "TKT-204",
        "title": "Email Flow Disruption",
        "description": "External emails delayed 2-4 hours. Internal email working. Message tracking shows messages stuck in submission queue. Transport service running. Recent Exchange CU update installed.",
        "category": "software",
        "priority": TicketPriority.HIGH,
        "requester": "messaging-team@company.com",
        "required_fixes": {
            "check_transport_service", "examine_message_queues", "verify_connector_status",
            "check_antivirus_integration", "review_recent_updates", "check_dns_mx_records",
            "analyze_mail_flow_rules", "verify_certificate_status"
        },
    },
    {
        "id": "TKT-205",
        "title": "CI/CD Pipeline Failure",
        "description": "Builds failing across multiple projects with 'Agent unreachable' errors. Kubernetes cluster showing pending pods. Resource quota not exceeded. Issue started after node pool auto-scaling event.",
        "category": "software",
        "priority": TicketPriority.HIGH,
        "requester": "devops-team@company.com",
        "required_fixes": {
            "check_node_status", "verify_agent_pools", "check_network_policies",
            "examine_pod_events", "check_storage_provisioner", "review_scaling_events",
            "verify_dns_resolution", "check_resource_limits"
        },
    },
]


KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "KB-001",
        "category": "access",
        "keywords": ["password", "reset", "forgot", "login", "account"],
        "solution": "Reset password in AD, require change at next login, send temp password via secure channel",
        "success_rate": 0.95,
        "avg_resolution_time": 10,
    },
    {
        "id": "KB-002",
        "category": "access",
        "keywords": ["vpn", "remote", "access", "connection", "tunnel"],
        "solution": "Verify AD group membership, provision VPN profile, send configuration instructions",
        "success_rate": 0.88,
        "avg_resolution_time": 20,
    },
    {
        "id": "KB-003",
        "category": "hardware",
        "keywords": ["printer", "offline", "printing", "queue", "spooler"],
        "solution": "Clear print spooler, restart print service, verify network connectivity, check driver",
        "success_rate": 0.82,
        "avg_resolution_time": 15,
    },
    {
        "id": "KB-004",
        "category": "software",
        "keywords": ["email", "sync", "mobile", "exchange", "phone"],
        "solution": "Remove and re-add account, verify Exchange ActiveSync enabled, check device compliance",
        "success_rate": 0.90,
        "avg_resolution_time": 25,
    },
    {
        "id": "KB-005",
        "category": "hardware",
        "keywords": ["monitor", "display", "screen", "no signal", "dual"],
        "solution": "Check display settings for extended/duplicate mode, verify cable connections, update graphics driver",
        "success_rate": 0.85,
        "avg_resolution_time": 20,
    },
    {
        "id": "KB-101",
        "category": "network",
        "keywords": ["intermittent", "connection", "drops", "adapter", "network"],
        "solution": "Update network drivers, check cable integrity, test different switch port, monitor for interference",
        "success_rate": 0.75,
        "avg_resolution_time": 45,
    },
    {
        "id": "KB-102",
        "category": "software",
        "keywords": ["database", "timeout", "connection", "crm", "sql"],
        "solution": "Check connection pool settings, verify firewall rules, restart database service, review query performance",
        "success_rate": 0.70,
        "avg_resolution_time": 60,
    },
    {
        "id": "KB-103",
        "category": "access",
        "keywords": ["access denied", "permissions", "share", "fileserver"],
        "solution": "Verify AD group membership, check NTFS permissions, reset Kerberos tickets, verify path exists",
        "success_rate": 0.78,
        "avg_resolution_time": 30,
    },
    {
        "id": "KB-104",
        "category": "software",
        "keywords": ["crash", "adobe", "creative", "startup", "error"],
        "solution": "Update graphics drivers, reset preferences, disable GPU acceleration, check available memory",
        "success_rate": 0.65,
        "avg_resolution_time": 50,
    },
    {
        "id": "KB-105",
        "category": "network",
        "keywords": ["ssl", "certificate", "expired", "warning", "https"],
        "solution": "Renew certificate from CA, update bindings, clear client cache, verify intermediate certs",
        "success_rate": 0.92,
        "avg_resolution_time": 40,
    },
    {
        "id": "KB-201",
        "category": "network",
        "keywords": ["replication", "dfs", "branch", "site", "multi-site"],
        "solution": "Check DFS health, verify WAN connectivity, examine replication schedule, check service accounts, analyze event logs",
        "success_rate": 0.55,
        "avg_resolution_time": 120,
    },
    {
        "id": "KB-202",
        "category": "access",
        "keywords": ["authentication", "ldap", "login", "ad", "sso", "degradation"],
        "solution": "Check AD controller health, verify LDAP connectivity, examine global catalog status, check DNS replication, review security logs",
        "success_rate": 0.50,
        "avg_resolution_time": 150,
    },
    {
        "id": "KB-203",
        "category": "hardware",
        "keywords": ["san", "storage", "performance", "latency", "cache"],
        "solution": "Check cache status, analyze IO patterns, verify controller health, check for rebuilds, examine queue depths",
        "success_rate": 0.45,
        "avg_resolution_time": 180,
    },
]

SYSTEM_COMPONENTS: List[Dict[str, Any]] = [
    {
        "name": "Active Directory",
        "status": "operational",
        "related_categories": ["access", "authentication"],
    },
    {
        "name": "VPN Gateway",
        "status": "operational",
        "related_categories": ["access", "network"],
    },
    {
        "name": "Exchange Server",
        "status": "operational",
        "related_categories": ["software", "email"],
    },
    {
        "name": "File Server",
        "status": "operational",
        "related_categories": ["access", "storage"],
    },
    {
        "name": "Database Cluster",
        "status": "operational",
        "related_categories": ["software", "database"],
    },
    {
        "name": "Print Server",
        "status": "operational",
        "related_categories": ["hardware", "printing"],
    },
    {
        "name": "DNS Server",
        "status": "operational",
        "related_categories": ["network", "infrastructure"],
    },
    {
        "name": "SAN Storage",
        "status": "operational",
        "related_categories": ["hardware", "storage"],
    },
    {
        "name": "Network Core",
        "status": "operational",
        "related_categories": ["network", "infrastructure"],
    },
    {
        "name": "Kubernetes Cluster",
        "status": "operational",
        "related_categories": ["software", "infrastructure"],
    },
]


def create_ticket(template: Dict[str, Any]) -> Ticket:
    """Create a Ticket object from template."""
    now = datetime.now()
    ticket = Ticket(
        id=template["id"],
        title=template["title"],
        description=template["description"],
        category=template["category"],
        priority=template["priority"],
        status=TicketStatus.OPEN,
        created_at=now - timedelta(hours=2),  # Created 2 hours ago
        requester=template["requester"],
        required_fixes=set(template.get("required_fixes", [])),
    )
    return ticket


def get_knowledge_base() -> List[KnowledgeBaseEntry]:
    """Get all knowledge base entries."""
    return [KnowledgeBaseEntry(**entry) for entry in KNOWLEDGE_BASE]


def get_system_components() -> Dict[str, SystemComponent]:
    """Get all system components."""
    now = datetime.now()
    return {
        comp["name"]: SystemComponent(
            name=comp["name"],
            status=comp["status"],
            last_checked=now,
            related_categories=comp["related_categories"],
        )
        for comp in SYSTEM_COMPONENTS
    }


def get_tickets_by_difficulty(difficulty: str) -> List[Ticket]:
    """Get tickets for specified difficulty level."""
    if difficulty == "easy":
        return [create_ticket(t) for t in EASY_TICKETS]
    elif difficulty == "medium":
        return [create_ticket(t) for t in MEDIUM_TICKETS]
    elif difficulty == "hard":
        return [create_ticket(t) for t in HARD_TICKETS]
    else:
        return [create_ticket(t) for t in EASY_TICKETS[:2]]  # Default subset
