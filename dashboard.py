import os
import argparse
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from rich.prompt import Prompt

from infrastructure.database.connection import DatabaseConnectionManager
from domain.opportunity import OpportunityStatus, Interaction, InteractionType, ApplicationEvent, ApplicationEventType
from domain.opportunity import Reminder, Document
from infrastructure.repositories.sqlite_opportunity_repo import SqliteOpportunityRepository
from infrastructure.storage.local_storage import LocalStorageEngine
import uuid
import os
from datetime import datetime

def get_repository(db_path: str):
    conn_manager = DatabaseConnectionManager(db_path)
    resolved_path = conn_manager.db_path
    
    if not os.path.exists(resolved_path):
        console = Console()
        console.print(f"[yellow]Database file '{resolved_path}' not found. Initializing a fresh database...[/yellow]")
        from infrastructure.database.migrations import run_idempotent_initialization
        run_idempotent_initialization(resolved_path)
        console.print(f"[bold green]Successfully initialized fresh database at '{resolved_path}'.[/bold green]")
        
    return SqliteOpportunityRepository(conn_manager)

def list_opportunities(repo, status_filter: Optional[str] = None):
    console = Console()
    status_enum = None
    if status_filter:
        try:
            status_enum = OpportunityStatus(status_filter)
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid status '{status_filter}'. Valid statuses are: {[s.value for s in OpportunityStatus]}")
            return

    opportunities = repo.get_all(status=status_enum)
    
    if not opportunities:
        console.print("[yellow]No opportunities found matching criteria.[/yellow]")
        return
        
    table = Table(title="Opportunity Cases Dashboard")
    
    table.add_column("ID (Business ID)", justify="left", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Company", style="green")
    table.add_column("Score", justify="right", style="blue")
    table.add_column("Status", justify="right", style="bold yellow")
    
    for opp in opportunities:
        score_str = f"{opp.confidence_score * 100:.0f}%" if opp.confidence_score is not None else "N/A"
        table.add_row(
            str(opp.id),
            opp.title,
            opp.company,
            score_str,
            opp.status.value
        )
        
    console.print(table)
    console.print(f"\n[dim]Total Cases: {len(opportunities)}[/dim]")

def view_opportunity(repo, business_id: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    # Build main detail panel
    details_text = Text()
    details_text.append(f"Title: ", style="bold")
    details_text.append(f"{opp.title}\n")
    details_text.append(f"Company: ", style="bold")
    details_text.append(f"{opp.company}\n")
    details_text.append(f"Status: ", style="bold")
    details_text.append(f"{opp.status.value}\n", style="yellow")
    details_text.append(f"Confidence Score: ", style="bold")
    score_str = f"{opp.confidence_score * 100:.0f}%" if opp.confidence_score is not None else "N/A"
    details_text.append(f"{score_str}\n", style="blue")
    
    console.print(Panel(details_text, title=f"Opportunity: {opp.id}", border_style="cyan"))
    
    # Render Contacts / Interactions
    if opp.interactions:
        interaction_table = Table(title="Interactions & Contacts", show_header=True, header_style="bold magenta")
        interaction_table.add_column("Date")
        interaction_table.add_column("Type")
        interaction_table.add_column("Contact Name")
        interaction_table.add_column("Contact Email")
        interaction_table.add_column("Notes")
        
        for i in opp.interactions:
            c_name = f"{i.contact.first_name} {i.contact.last_name}".strip() if i.contact else "N/A"
            c_email = i.contact.email if i.contact and i.contact.email else "N/A"
            
            interaction_table.add_row(
                i.interaction_date.strftime("%Y-%m-%d %H:%M"),
                i.interaction_type.value,
                c_name,
                c_email,
                i.notes or ""
            )
            
        console.print(interaction_table)
    else:
        console.print("[dim]No interactions recorded for this opportunity.[/dim]")
        
    # Render Documents
    if opp.documents:
        doc_table = Table(title="Attached Documents", show_header=True, header_style="bold green")
        doc_table.add_column("Type")
        doc_table.add_column("Name")
        doc_table.add_column("Storage Path")
        
        for doc in opp.documents:
            doc_table.add_row(
                doc.document_type,
                doc.name,
                doc.file_path
            )
        console.print(doc_table)
    else:
        console.print("[dim]No documents attached.[/dim]")
        
    # Raw JSON Data Display
    if opp.raw_ingestion_data:
        console.print("\n[bold]Raw Ingestion Data:[/bold]")
        raw_json = json.dumps(opp.raw_ingestion_data, indent=2)
        console.print(Panel(raw_json, border_style="green"))

def review_opportunities(repo):
    console = Console()
    opportunities = repo.get_all()
    detected_cases = [opp for opp in opportunities if opp.status == OpportunityStatus.Detected]
    
    if not detected_cases:
        console.print("[green]Inbox zero! No opportunities pending Human Review.[/green]")
        return
        
    console.print(f"\n[bold yellow]--- Human Review Queue ({len(detected_cases)} cases) ---[/bold yellow]")
    
    for opp in detected_cases:
        # Display case
        console.clear()
        view_opportunity(repo, opp.id)
        
        console.print("\n[bold cyan]Action Required:[/bold cyan]")
        console.print("[E]valuate (Move to Evaluating)")
        console.print("[D]rop (Move to Closed)")
        console.print("[S]kip (Leave in Detected for later)")
        
        action = Prompt.ask("Select action", choices=["E", "e", "D", "d", "S", "s"], default="S")
        
        if action.upper() == "S":
            console.print("[dim]Skipping...[/dim]")
            continue
        elif action.upper() == "E":
            opp.transition_to(OpportunityStatus.Evaluating)
            repo.update(opp)
            console.print(f"[bold green]Opportunity {opp.id} moved to Evaluating.[/bold green]")
        elif action.upper() == "D":
            opp.transition_to(OpportunityStatus.Closed)
            repo.update(opp)
            console.print(f"[bold red]Opportunity {opp.id} Closed.[/bold red]")

def log_activity(repo, business_id: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    console.print(f"\n[bold cyan]Logging Activity for: {opp.title} at {opp.company}[/bold cyan]")
    activity_type = Prompt.ask("What do you want to log?", choices=["Interaction", "Event"], default="Interaction")
    
    if activity_type == "Interaction":
        console.print("Available types: Call, Email, Meeting, Other")
        i_type_str = Prompt.ask("Type", default="Email")
        try:
            i_type = InteractionType(i_type_str)
        except ValueError:
            i_type = InteractionType.Other
            
        notes = Prompt.ask("Notes")
        
        interaction = Interaction(
            id=str(uuid.uuid4()),
            interaction_type=i_type,
            interaction_date=datetime.utcnow(),
            notes=notes
        )
        opp.add_interaction(interaction)
        repo.update(opp)
        console.print("[bold green]Interaction logged successfully![/bold green]")
        
    else:
        console.print("Available types: ApplicationSubmitted, InterviewScheduled, InterviewCompleted, OfferReceived, OfferAccepted, OfferDeclined, Rejected")
        e_type_str = Prompt.ask("Type", default="InterviewScheduled")
        try:
            e_type = ApplicationEventType(e_type_str)
        except ValueError:
            console.print("[bold red]Invalid event type.[/bold red]")
            return
            
        notes = Prompt.ask("Notes (optional)", default="")
        
        event = ApplicationEvent(
            id=str(uuid.uuid4()),
            event_type=e_type,
            event_date=datetime.utcnow(),
            notes=notes if notes else None
        )
        opp.add_event(event)
        repo.update(opp)
        console.print("[bold green]Application Event logged successfully![/bold green]")

def view_agenda(repo):
    console = Console()
    reminders = repo.get_pending_reminders()
    
    if not reminders:
        console.print("[green]Your agenda is clear! No pending reminders.[/green]")
        return
        
    table = Table(title="Agenda (Pending Reminders)", show_lines=True)
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Opportunity", style="magenta")
    table.add_column("Business ID", style="dim")
    table.add_column("Task / Note", style="bold white")
    
    for rem, title, bus_id in reminders:
        table.add_row(
            rem.reminder_date.strftime("%Y-%m-%d %H:%M"),
            title,
            bus_id,
            rem.note
        )
        
    console.print(table)

def sync_email(repo):
    console = Console()
    console.print("[cyan]Connecting to IMAP Server to sync emails...[/cyan]")
    
    try:
        from infrastructure.adapters.email_adapter import EmailAdapter
        from core.ingestion.pipeline import IngestionPipeline
        from infrastructure.ai.llm_extractor import GeminiAIExtractor
        from core.intelligence.scorer import OpportunityScorer
        from core.ingestion.deduplicator import DuplicateDetector
        from infrastructure.adapters.gemini_provider import GeminiProvider
        
        adapter = EmailAdapter()
        extractor = GeminiAIExtractor()
        provider = GeminiProvider()
        scorer = OpportunityScorer(llm_provider=provider)
        deduplicator = DuplicateDetector(repository=repo)
        
        pipeline = IngestionPipeline(
            repository=repo, 
            ai_extractor=extractor, 
            scorer=scorer,
            deduplicator=deduplicator
        )
        
        results = pipeline.ingest_batch(adapter)
        
        if not results:
            console.print("[green]Inbox zero! No new unread opportunities to sync.[/green]")
            return
            
        console.print(f"\n[bold green]Successfully ingested {len(results)} new opportunities from email![/bold green]")
        for opp in results:
            console.print(f"- [cyan]{opp.id}[/cyan] | {opp.title} at {opp.company}")
            
    except ValueError as e:
        console.print("[bold green]URL successfully synced and ingested![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Sync failed:[/bold red] {e}")

def prepare_audit():
    console = Console()
    console.print("[cyan]Preparing codebase snapshot for audit...[/cyan]")
    try:
        import sys
        from pathlib import Path
        
        # Add project root to sys.path if not there
        project_root = Path(__file__).resolve().parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        from scripts.audit_exporter import AuditExporter
        
        exporter = AuditExporter(root_dir=str(project_root))
        snapshot_path = exporter.generate_snapshot()
        
        console.print(f"[bold green]Snapshot successfully generated![/bold green]")
        console.print(f"Absolute path: [cyan]{snapshot_path}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Failed to prepare audit snapshot:[/bold red] {e}")

def register_offer(repo, business_id: str, base: float, bonus: float, equity: float, benefits: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    try:
        import uuid
        from domain.opportunity import Offer, OpportunityStatus
        
        offer = Offer(
            id=str(uuid.uuid4()),
            base_salary=base,
            bonus_percentage=bonus,
            equity_value=equity,
            benefits_summary=benefits
        )
        
        opp.add_offer(offer)
        opp.transition_to(OpportunityStatus.Offer)
        repo.update(opp)
        console.print(f"[bold green]Offer successfully registered for {opp.company}! Status updated to Offer.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to register offer:[/bold red] {e}")

def evaluate_offer(repo, business_id: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    if not opp.offers:
        console.print(f"[bold red]Error:[/bold red] No offers registered for '{opp.company}'. Register an offer first.")
        return
        
    latest_offer = opp.offers[-1]
    
    console.print(f"[cyan]Evaluating latest offer for {opp.company}...[/cyan]")
    try:
        from core.intelligence.negotiator import NegotiationStrategist
        from infrastructure.adapters.gemini_provider import GeminiProvider
        
        provider = GeminiProvider()
        strategist = NegotiationStrategist(llm_provider=provider)
        json_output = strategist.evaluate_offer(opp, latest_offer)
        
        import json
        parsed = json.loads(json_output)
        
        console.print("\n[bold magenta]=== EXECUTIVE NEGOTIATION BRIEFING ===[/bold magenta]")
        console.print(f"\n[bold cyan]Financial Gap Analysis:[/bold cyan]\n{parsed.get('financial_gap_analysis', 'N/A')}")
        
        console.print("\n[bold cyan]Leverage Points:[/bold cyan]")
        for lp in parsed.get('leverage_points', []):
            console.print(f"- {lp}")
            
        console.print(f"\n[bold cyan]Suggested Counter-Offer Strategy:[/bold cyan]\n{parsed.get('suggested_counter_offer_strategy', 'N/A')}")
        
        console.print("\n[bold cyan]Risk Factors:[/bold cyan]")
        for rf in parsed.get('risk_factors', []):
            console.print(f"- {rf}")
            
        console.print("\n[bold magenta]========================================[/bold magenta]\n")
        
    except Exception as e:
        console.print(f"[bold red]Failed to evaluate offer:[/bold red] {e}")

def attach_document(repo, business_id: str, file_path: str, doc_type: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    storage = LocalStorageEngine()
    try:
        stored_path = storage.attach_file(file_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Storage Error:[/bold red] {e}")
        return
        
    filename = os.path.basename(file_path)
    
    doc = Document(
        id=str(uuid.uuid4()),
        name=filename,
        file_path=stored_path,
        document_type=doc_type
    )
    
    opp.add_document(doc)
    repo.update(opp)
    console.print(f"[bold green]Successfully attached '{filename}' to {opp.company}![/bold green]")
    console.print(f"[dim]Stored internally at: {stored_path}[/dim]")

def view_analytics(repo):
    console = Console()
    analytics = repo.get_pipeline_analytics()
    
    # Render Status Distribution Table
    dist_table = Table(title="Pipeline Status Distribution", show_header=True, header_style="bold blue")
    dist_table.add_column("Status", style="cyan")
    dist_table.add_column("Count", justify="right", style="green")
    
    from domain.opportunity import OpportunityStatus
    for status in OpportunityStatus:
        count = analytics["status_distribution"].get(status.value, 0)
        dist_table.add_row(status.value, str(count))
        
    dist_table.add_section()
    dist_table.add_row("[bold]Total Opportunities[/bold]", f"[bold green]{analytics['total_cases']}[/bold green]")
    
    # Render Funnel & Conversion Metrics
    funnel = analytics["funnel"]
    rates = analytics["conversion_rates"]
    
    funnel_table = Table(title="Conversion Funnel (Applied -> Offer)", show_header=True, header_style="bold magenta")
    funnel_table.add_column("Stage", style="cyan")
    funnel_table.add_column("Count", justify="right", style="green")
    funnel_table.add_column("Conversion Rate", justify="right", style="yellow")
    
    funnel_table.add_row("Applied", str(funnel["applied"]), "-")
    funnel_table.add_row("Interviewed", str(funnel["interviewed"]), f"{rates['applied_to_interview']}%")
    funnel_table.add_row("Offers", str(funnel["offers"]), f"{rates['interview_to_offer']}%")
    funnel_table.add_section()
    funnel_table.add_row("[bold]Overall Win Rate[/bold]", "", f"[bold green]{rates['overall_win_rate']}%[/bold green]")
    
    console.print("\n")
    console.print(dist_table)
    console.print("\n")
    console.print(funnel_table)
    console.print("\n")

def export_snapshot(repo, business_id: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    console.print("[cyan]Generating Strategic AI Briefing...[/cyan]")
    try:
        from core.intelligence.strategist import InterviewStrategist
        from infrastructure.adapters.gemini_provider import GeminiProvider
        from infrastructure.exporters.snapshot_exporter import SnapshotExporter
        
        provider = GeminiProvider()
        strategist = InterviewStrategist(llm_provider=provider)
        strategy = strategist.generate_strategy(opp)
        
        exporter = SnapshotExporter()
        export_path = exporter.export(opp, strategy)
        
        console.print("[bold green]Snapshot strategy briefing successfully generated![/bold green]")
        console.print(f"File stored at: [cyan]{export_path}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Failed to generate snapshot:[/bold red] {e}")

def draft_communication(repo, business_id: str, intent: str):
    console = Console()
    opp = repo.get_by_business_id(business_id)
    if not opp:
        console.print(f"[bold red]Error:[/bold red] Opportunity with ID '{business_id}' not found.")
        return
        
    console.print(f"[cyan]Drafting executive communication for intent: '{intent}'...[/cyan]")
    try:
        from core.intelligence.drafter import ExecutiveDrafter
        from infrastructure.adapters.gemini_provider import GeminiProvider
        
        provider = GeminiProvider()
        drafter = ExecutiveDrafter(llm_provider=provider)
        draft_text, export_path = drafter.draft_communication(opp, intent)
        
        console.print("[bold green]Draft generated successfully![/bold green]")
        console.print("\n" + "="*50)
        console.print(draft_text)
        console.print("="*50 + "\n")
        console.print(f"File stored at: [cyan]{export_path}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Failed to generate draft:[/bold red] {e}")

def search_opportunities(repo, keyword: str):
    console = Console()
    console.print(f"[cyan]Searching for keyword '{keyword}'...[/cyan]")
    opportunities = repo.search(keyword)
    
    if not opportunities:
        console.print(f"[yellow]No opportunities found matching '{keyword}'.[/yellow]")
        return
        
    table = Table(title=f"Search Results for '{keyword}'")
    table.add_column("ID (Business ID)", justify="left", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Company", style="green")
    table.add_column("Status", justify="right", style="bold yellow")
    
    for opp in opportunities:
        table.add_row(
            str(opp.id),
            opp.title,
            opp.company,
            opp.status.value
        )
        
    console.print(table)
    console.print(f"\n[dim]Total Matched Cases: {len(opportunities)}[/dim]")

def backup_system(db_path: str):
    console = Console()
    console.print("[cyan]Archiving system data (SQLite database & vault attachments)...[/cyan]")
    
    try:
        storage = LocalStorageEngine()
        backup_file = storage.create_backup(db_path)
        console.print("[bold green]Backup successfully compiled![/bold green]")
        console.print(f"Archive file: [cyan]{backup_file}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Failed to create backup:[/bold red] {e}")

def show_network(repo):
    console = Console()
    console.print("[cyan]Generating Global Network & Rolodex read-model...[/cyan]")
    
    network = repo.get_global_network()
    
    if not network:
        console.print("[yellow]No contacts found in the system.[/yellow]")
        return
        
    table = Table(title="Global Contact Rolodex & Sponsor Graph")
    table.add_column("Name", style="cyan")
    table.add_column("Company", style="green")
    table.add_column("Email", style="magenta")
    table.add_column("Phone", style="blue")
    table.add_column("Interactions", justify="right", style="bold yellow")
    table.add_column("Opportunities", justify="right", style="bold yellow")
    
    for c in network:
        table.add_row(
            c["name"],
            c["company"],
            c["email"],
            c["phone"],
            str(c["interactions"]),
            str(c["opportunities"])
        )
        
    console.print(table)
    console.print(f"\n[dim]Total Network Contacts: {len(network)}[/dim]")

def main():
    parser = argparse.ArgumentParser(description="CIOS Dashboard & Operations CLI")
    parser.add_argument("--db", type=str, default=None, help="Path to the SQLite database")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    list_parser = subparsers.add_parser("list", help="List all opportunities")
    list_parser.add_argument("--status", type=str, default=None, help="Filter opportunities by status")
    
    search_parser = subparsers.add_parser("search", help="Search across critical text fields")
    search_parser.add_argument("keyword", type=str, help="The search keyword")
    
    view_parser = subparsers.add_parser("view", help="View a specific opportunity's details")
    view_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    
    subparsers.add_parser("review", help="Interactive Human Review queue for Detected cases")
    
    log_parser = subparsers.add_parser("log", help="Log an interaction or event to a specific opportunity")
    log_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    
    subparsers.add_parser("agenda", help="View all pending reminders across all active cases")
    
    subparsers.add_parser("sync-email", help="Sync unread opportunities directly from the configured IMAP inbox")
    
    attach_parser = subparsers.add_parser("attach", help="Attach a local file/CV to an opportunity")
    attach_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    attach_parser.add_argument("file_path", type=str, help="The local file path to the document")
    attach_parser.add_argument("--type", type=str, default="General", help="The type of document (e.g., CV, CoverLetter, General)")
    
    subparsers.add_parser("analytics", help="View high-level pipeline funnel and health metrics")
    
    snapshot_parser = subparsers.add_parser("snapshot", help="Generate and export an opportunity strategy snapshot")
    snapshot_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    
    subparsers.add_parser("backup", help="Create a timestamped backup archive of the system database and attachments")
    
    subparsers.add_parser("network", help="View the global network rolodex sorted by interaction frequency")
    
    draft_parser = subparsers.add_parser("draft", help="Draft an executive email based on case context")
    draft_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    draft_parser.add_argument("--intent", type=str, required=True, help="Intent of the communication (e.g., 'thank_you', 'counter_offer')")
    
    audit_parser = subparsers.add_parser("audit", help="Identify stalled opportunities in the pipeline")
    audit_parser.add_argument("--days", type=int, default=7, help="Number of days inactive to consider stale (default: 7)")
    
    sync_url_parser = subparsers.add_parser("sync-url", help="Sync an opportunity directly from a URL")
    sync_url_parser.add_argument("url", type=str, help="The URL of the job posting")
    
    register_offer_parser = subparsers.add_parser("register-offer", help="Register a financial offer for a case")
    register_offer_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    register_offer_parser.add_argument("--base", type=float, required=True, help="Base salary (e.g., 250000)")
    register_offer_parser.add_argument("--bonus", type=float, required=True, help="Bonus percentage (e.g., 20.5)")
    register_offer_parser.add_argument("--equity", type=float, required=True, help="Equity value (e.g., 1000000)")
    register_offer_parser.add_argument("--benefits", type=str, default="", help="Optional benefits summary string")
    
    evaluate_offer_parser = subparsers.add_parser("evaluate-offer", help="Evaluate the latest offer and generate negotiation strategy")
    evaluate_offer_parser.add_argument("id", type=str, help="The Business ID of the opportunity")
    
    prepare_audit_parser = subparsers.add_parser("prepare-audit", help="Export codebase snapshot for algorithm audit")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # We pass the db path directly for backup
    if args.command == "backup":
        backup_system(args.db)
        return
        
    repo = get_repository(args.db)
    
    if args.command == "list":
        list_opportunities(repo, args.status)
    elif args.command == "search":
        search_opportunities(repo, args.keyword)
    elif args.command == "view":
        view_opportunity(repo, args.id)
    elif args.command == "review":
        review_opportunities(repo)
    elif args.command == "log":
        log_activity(repo, args.id)
    elif args.command == "agenda":
        view_agenda(repo)
    elif args.command == "sync-email":
        sync_email(repo)
    elif args.command == "attach":
        attach_document(repo, args.id, args.file_path, args.type)
    elif args.command == "analytics":
        view_analytics(repo)
    elif args.command == "snapshot":
        export_snapshot(repo, args.id)
    elif args.command == "network":
        show_network(repo)
    elif args.command == "draft":
        draft_communication(repo, args.id, args.intent)
    elif args.command == "audit":
        audit_pipeline(repo, args.days)
    elif args.command == "sync-url":
        sync_url_command(repo, args.url)
    elif args.command == "register-offer":
        register_offer(repo, args.id, args.base, args.bonus, args.equity, args.benefits)
    elif args.command == "evaluate-offer":
        evaluate_offer(repo, args.id)
    elif args.command == "prepare-audit":
        prepare_audit()

if __name__ == "__main__":
    main()
