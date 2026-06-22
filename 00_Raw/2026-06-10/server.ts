import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Initialize GoogleGenAI client lazy / safely
let aiClient: GoogleGenAI | null = null;
function getAiClient() {
  if (!aiClient) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.warn("⚠️ GEMINI_API_KEY environment variable is not defined");
    }
    aiClient = new GoogleGenAI({
      apiKey: apiKey || "",
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        },
      },
    });
  }
  return aiClient;
}

// API endpoint for analysis and marketing bullet copy generation based on property info
app.post("/api/gemini/analyze", async (req, res) => {
  try {
    const { rawText } = req.body;
    if (!rawText) {
      return res.status(400).json({ error: "rawText is required" });
    }

    const ai = getAiClient();
    const prompt = `You are a professional South Korean real estate agent specializing in redevelopment (재개발) and reconstruction (재건축) properties.
Analyze the following property raw text info or notes. Extract or generate the property banner information in Korean.

The raw text may contain:
- Area or zone name (e.g., "북아현 2구역", "한남3구역")
- Type or size (e.g., "84타입", "59타입")
- Financial values (in Korean currency like 억, 천만원, etc.):
  - Selling Price (매매가)
  - Premium (프리미엄) - the value added above appraised value
  - Appraised or right value (권리가)
  - Rental deposit or lessee's rent (임대/전세/보증금)
  - Estimated Move-In Market Price or expected price (예상시세)
  - Member purchase price (조합원분양가)
  - size in m² (e.g. 59m², 84m²)
  - phone or custom info (전화번호, 플랫폼명, 이름)
- Highlight bullet items: Extract or compose 5 appealing, highly professional key points about the property (e.g. status of administrative authorization, relocation fee terms, premium reasonability, transport, school districts, investment margins). Keep each bullet concise and impact-driven (similar in tone to: "관처인가 임박 (26년 2월 예정)", "조합원분양가 : 59타입 8.4억 / 84타입 10.3억").

Please output a strictly valid JSON response that contains the following properties.
Use the best calculations based on Korean real estate knowledge if some values are missing, or provide realistic placeholders:
- "area": string (e.g., "북아현 2구역")
- "type": string (e.g., "84타입")
- "sellingPrice": string (e.g., "15억")
- "premium": string (e.g., "5억")
- "appraisedValue": string (e.g., "10억")
- "rent": string (e.g., "7억")
- "totalPurchasePrice": string (e.g., "23.7억", which is usually appraised value + premium + additional payment, or estimated)
- "safetyMargin": string (e.g., "6.3억")
- "highlights": string[] (Exactly 5 string items. Each item must be a short punchy bullet line, maximum 30 characters in Korean)
- "size": string (e.g., "84㎡")
- "acquisitionTax": string (e.g., "5,250만원" or "예상 5,250만원")
- "platform": string (e.g., "대한민국 재개발 재건축 NO.1 플랫폼")
- "contact": string (e.g., "홍길동 : 010-1234-5678")
- "footer": string (e.g., "북아현2구역 가장 최신 진행상황은 아래▼ 자세히 나와있습니다.")

Raw property notes:
"""
${rawText}
"""

Ensure the output is JSON only.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
      },
    });

    const text = response.text || "{}";
    const parsedData = JSON.parse(text);
    return res.json(parsedData);
  } catch (error: any) {
    console.error("Gemini API error:", error);
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

// Setup Vite Dev server or Production static serve
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
  });
}

startServer();
