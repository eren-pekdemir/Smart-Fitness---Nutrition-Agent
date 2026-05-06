"""Smart Fitness & Nutrition Agent — interactive CLI entry point."""

from agent.fitness_agent import FitnessAgent


BANNER = """
╔══════════════════════════════════════════════╗
║   Smart Fitness & Nutrition Agent  v1.0      ║
║   Type 'quit' to exit, 'reset' to restart   ║
╚══════════════════════════════════════════════╝
"""

EXAMPLES = """
Example prompts:
  - I had a protein shake and 2 bananas for breakfast
  - Log 200g of chicken breast and 150g of white rice
  - What are my macros for today?
  - Calculate my daily calorie needs: 80kg, 180cm, 25 years old male, active, gain muscle
  - Show my recent meal history
"""


def main():
    print(BANNER)
    print(EXAMPLES)

    try:
        agent = FitnessAgent()
    except EnvironmentError as e:
        print(f"[Setup Error] {e}")
        print("Please copy .env.example to .env and add your ANTHROPIC_API_KEY.")
        return

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("Conversation history cleared.")
            continue

        response = agent.chat(user_input)
        print(f"\nAssistant: {response}\n")


if __name__ == "__main__":
    main()
