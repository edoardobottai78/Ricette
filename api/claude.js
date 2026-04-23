export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { action, imageBase64, mediaType, ingredienti } = req.body;
  const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY;

  if (!ANTHROPIC_KEY) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY non configurata' });
  }

  try {
    // ── AZIONE 1: estrai ricetta da screenshot Instagram ──────────────────
    if (action === 'extract') {
      if (!imageBase64 || !mediaType) {
        return res.status(400).json({ error: 'Immagine mancante' });
      }

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': ANTHROPIC_KEY,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          model: 'claude-opus-4-5',
          max_tokens: 1024,
          messages: [{
            role: 'user',
            content: [
              {
                type: 'image',
                source: {
                  type: 'base64',
                  media_type: mediaType,
                  data: imageBase64
                }
              },
              {
                type: 'text',
                text: `Sei un assistente culinario. Analizza questo screenshot e estrai la ricetta.
Rispondi SOLO con un oggetto JSON valido, senza testo aggiuntivo, in questo formato esatto:
{
  "titolo": "nome della ricetta",
  "ingredienti": ["ingrediente 1", "ingrediente 2"],
  "procedimento": "testo del procedimento"
}
Se non trovi una ricetta nell'immagine, rispondi con:
{"errore": "Nessuna ricetta trovata nell'immagine"}`
              }
            ]
          }]
        })
      });

      const data = await response.json();
      if (!response.ok) {
        return res.status(500).json({ error: data.error?.message || 'Errore Claude API' });
      }

      const testo = data.content[0].text.trim();
      try {
        const ricetta = JSON.parse(testo);
        return res.status(200).json(ricetta);
      } catch {
        return res.status(500).json({ error: 'Risposta AI non valida' });
      }
    }

    // ── AZIONE 2: calcola calorie dagli ingredienti ───────────────────────
    if (action === 'calorie') {
      if (!ingredienti || !ingredienti.length) {
        return res.status(400).json({ error: 'Ingredienti mancanti' });
      }

      const listaIng = ingredienti.join('\n');

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': ANTHROPIC_KEY,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          model: 'claude-opus-4-5',
          max_tokens: 512,
          messages: [{
            role: 'user',
            content: `Sei un nutrizionista. Stima i valori nutrizionali per UNA PORZIONE di questa ricetta con questi ingredienti:

${listaIng}

Rispondi SOLO con un oggetto JSON valido, senza testo aggiuntivo:
{
  "kcal": 620,
  "carboidrati": 72,
  "proteine": 22,
  "grassi": 18,
  "fibre": 4
}
Usa solo numeri interi. Stima ragionevole per una porzione standard.`
          }]
        })
      });

      const data = await response.json();
      if (!response.ok) {
        return res.status(500).json({ error: data.error?.message || 'Errore Claude API' });
      }

      const testo = data.content[0].text.trim();
      try {
        const valori = JSON.parse(testo);
        return res.status(200).json(valori);
      } catch {
        return res.status(500).json({ error: 'Risposta AI non valida' });
      }
    }

    return res.status(400).json({ error: 'Azione non riconosciuta' });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
