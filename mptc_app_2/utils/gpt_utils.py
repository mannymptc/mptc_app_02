import openai
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_output_for_group(group, image_url, base_prompt):
    try:
        expected_cols = [
            "Size", "Colour", "Category", "Finish/Style", "Feature",
            "Care", "Composition", "Width", "Length", "Height"
        ]
        available_cols = [col for col in expected_cols if col in group.columns]
        product_info = group.iloc[0][available_cols].dropna().to_dict()
        product_info_text = "\n".join([f"{key}: {val}" for key, val in product_info.items()])

        full_prompt = f"{base_prompt.strip()}\n\nProduct Info:\n{product_info_text}"

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert e-commerce product copywriter and SEO strategist."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=1800,
            temperature=0.7
        )

        raw_text = response.choices[0].message.content

        # Parse titles and description
        titles = {}
        desc_lines = []
        current_block = None

        lines = raw_text.splitlines()
        for line in lines:
            if line.strip().startswith("Title 1:"):
                current_block = "Title 1"
                titles["Title 1"] = line.split("Title 1:")[-1].strip()
            elif line.strip().startswith("Title 2:"):
                current_block = "Title 2"
                titles["Title 2"] = line.split("Title 2:")[-1].strip()
            elif line.strip().startswith("Title 3:"):
                current_block = "Title 3"
                titles["Title 3"] = line.split("Title 3:")[-1].strip()
            elif line.strip().startswith("Title 4:"):
                current_block = "Title 4"
                titles["Title 4"] = line.split("Title 4:")[-1].strip()
            elif line.strip().startswith("Description:"):
                current_block = "Description"
            elif current_block == "Description":
                desc_lines.append(line.strip())

        # Replace "- " with "-->" for bullets
        description = "\n".join([
            line.replace("- ", "* ") if line.startswith("- ") else line
            for line in desc_lines if line
        ])

        return {
            "title_map": titles,
            "desc1": description.strip(),
            "gpt_raw_response": raw_text
        }

    except Exception as e:
        return {
            "title_map": {},
            "desc1": "",
            "gpt_raw_response": f"❌ GPT API Error: {e}"
        }
