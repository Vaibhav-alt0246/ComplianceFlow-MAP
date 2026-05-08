import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the tools (they are Tool objects in CrewAI 1.x)
from tools.pdf_reader import read_pdf_with_paragraphs, read_pdf_circular
from tools.db_manager import create_compliance_ticket


def test_pdf_processor():
    """Test the PDF processor tool."""
    print("=" * 60)
    print("Testing PDF Processor Tool")
    print("=" * 60)

    pdf_path = "data_assets/sample_rbi_circular.pdf"

    if not os.path.exists(pdf_path):
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   Skipping PDF extraction test.")
        return

    try:
        # In CrewAI 1.x, @tool wraps the function - access the underlying function
        text = read_pdf_with_paragraphs.func(pdf_path)
        print(f"✓ PDF extracted successfully. Total characters: {len(text)}")
        print(f"\nFirst 500 characters:")
        print("-" * 60)
        print(text[:500])
        print("-" * 60)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


def test_ticket_db():
    """Test the ticket database tool."""
    print("\n" + "=" * 60)
    print("Testing Ticket Database Tool")
    print("=" * 60)

    try:
        # In CrewAI 1.x, @tool wraps the function - access the underlying function
        result = create_compliance_ticket.func(
            task="Test Task",
            department="IT",
            explainability_trigger="Test Trigger",
            confidence_score="95"
        )
        print(f"✓ Database tool works: {result}")

        # Verify the database file was created
        db_path = "../database/compliance_tickets.db"
        abs_db_path = os.path.join(os.path.dirname(__file__), db_path)
        if os.path.exists(abs_db_path):
            print(f"✓ Database file exists at: {abs_db_path}")
        else:
            print(f"⚠️  Database file not found at expected path: {abs_db_path}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🧪 Testing Tools (Pure Python Functions)\n")

    test_pdf_processor()
    test_ticket_db()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
