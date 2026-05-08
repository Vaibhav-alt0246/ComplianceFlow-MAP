import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the tools (they are Tool objects in CrewAI 1.x)
from tools.pdf_reader import extract_text_from_pdf, read_pdf_circular
from tools.db_manager import create_compliance_ticket


def test_pdf_reader():
    """Test the PDF reader tool."""
    print("=" * 60)
    print("Testing PDF Reader Tool")
    print("=" * 60)

    # Test with a non-existent file to verify error handling
    try:
        result = extract_text_from_pdf("nonexistent.pdf")
        print("❌ ERROR: Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✓ Error handling works: {e}")

    # Test with the base_policies.txt (not a PDF, but will test the function exists)
    # For a real test, you would need an actual PDF file
    print("\n⚠️  Note: No sample PDF found in data/ directory.")
    print("   To fully test PDF reading, add a sample circular PDF to data/")
    print("   and update the test path accordingly.")

    return True


def test_database_tool():
    """Test the database tool."""
    print("\n" + "=" * 60)
    print("Testing Database Tool")
    print("=" * 60)

    # Test with dummy data
    try:
        # In CrewAI 1.x, @tool wraps the function - access the underlying function
        result = create_compliance_ticket.func(
            task="Implement 14-character password policy",
            department="IT_SECURITY",
            explainability_trigger="Policy requires minimum 14 characters",
            confidence_score="0.95"
        )
        print(f"✓ Database tool works: {result}")

        # Verify the database file was created
        db_path = "../database/compliance_tickets.db"
        abs_db_path = os.path.join(os.path.dirname(__file__), db_path)
        if os.path.exists(abs_db_path):
            print(f"✓ Database file created at: {abs_db_path}")
        else:
            print(f"⚠️  Database file not found at expected path: {abs_db_path}")

        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Running Tool Tests\n")

    pdf_test = test_pdf_reader()
    db_test = test_database_tool()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"PDF Reader: {'✓ PASS' if pdf_test else '❌ FAIL'}")
    print(f"Database Tool: {'✓ PASS' if db_test else '❌ FAIL'}")

    if pdf_test and db_test:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
