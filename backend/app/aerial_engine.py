import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv()

# Initialize OpenAI client only when API key is available to prevent startup crashes
_api_key = os.getenv("OPENAI_API_KEY")
client = None
if _api_key:
    try:
        client = OpenAI(api_key=_api_key)
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client: {e}")
else:
    print("Info: OPENAI_API_KEY not set. AerialEngine will use local heuristic fallback.")

class AerialEngine:
    @staticmethod
    def generate_reasoning(request_data: dict, math_context: dict, customer_stats: dict) -> str:
        """
        Calls OpenAI to generate pricing reasoning based on context.
        Falls back to a data-driven heuristic if OpenAI is unavailable.
        """
        system_prompt = """You are AerialEngine, an expert AI pricing agent for Systematic Wire Manufacturing.
Your goal is to explain to the sales team why a specific quotation price is recommended, and what that recommended price should be.

PRICING RULES TO STRICTLY FOLLOW:
1. For OLD/REPEAT customers: You must ensure they are kept happy to secure their loyalty. Suggest a "Loyalty Price" that is highly competitive and heavily influenced by their historical average price paid (if available), matching it or undercutting it slightly if it covers the Floor Price.
2. For NEW customers: You can deal with higher prices. Suggest a "Premium Price" based on the Standard Target Price to capture better margin.

INSTRUCTIONS:
- Read the context provided by the user.
- Recommend a specific price per MT.
- Keep your reasoning concise (3-4 short sentences). 
- Be professional, authoritative, and data-driven. 
- Do NOT generate conversational greetings (like "Hello"). Just provide the reasoning text directly.
"""

        hist_avg = math_context.get('historical_avg_price')
        hist_text = f"₹{hist_avg:,.2f}" if hist_avg else "No history for this exact item"

        user_prompt = f"""
--- CONTEXT ---
Customer Name: {customer_stats.get('name', 'Unknown')}
Is Repeat Customer: {customer_stats.get('is_repeat', False)}
Total Past Orders: {customer_stats.get('total_orders', 0)}

Product Requested: {request_data.get('product_type', '')} - {request_data.get('product_code', '')}

--- MATH & COSTS ---
- Floor Price (Absolute minimum, zero margin): ₹{math_context.get('floor_price_mt', 0):,.2f}
- Standard Target Price (Standard margin): ₹{math_context.get('target_price_mt', 0):,.2f}
- Customer's Historical Average Price for this item: {hist_text}

Based on the Pricing Rules, what is your recommended price and reasoning?
"""

        # Fallback: generate a data-driven heuristic response when OpenAI is unavailable
        if not client:
            floor = math_context.get('floor_price_mt', 0)
            target = math_context.get('target_price_mt', 0)
            cust_name = customer_stats.get('name', 'Customer')
            is_repeat = customer_stats.get('is_repeat', False)
            recommended = hist_avg if (hist_avg and hist_avg > target) else target

            if is_repeat:
                return (
                    f"Recommendation for repeat customer {cust_name}: ₹{recommended:,.2f}/MT. "
                    f"This loyalty price aligns with historical averages while covering the floor cost "
                    f"of ₹{floor:,.2f}/MT. Maintaining competitive pricing to protect this relationship."
                )
            else:
                return (
                    f"Recommendation for new customer {cust_name}: ₹{recommended:,.2f}/MT. "
                    f"Premium pricing captures a healthy margin above the floor cost of ₹{floor:,.2f}/MT "
                    f"while remaining competitive in the current steel market."
                )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"AerialEngine is offline or encountered an error: {str(e)}"

