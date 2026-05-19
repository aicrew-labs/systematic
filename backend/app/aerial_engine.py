import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AerialEngine:
    @staticmethod
    def generate_reasoning(request_data: dict, math_context: dict, customer_stats: dict) -> str:
        """
        Calls OpenAI to generate pricing reasoning based on context.
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
