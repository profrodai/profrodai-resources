import express from "express";
import { OrderClient } from "./client";

const app = express();
app.use(express.json());
const client = new OrderClient();

app.get("/orders/:id", (req, res) => {
  res.json(client.get(req.params.id));
});

app.get("/customers/:id/orders", (req, res) => {
  res.json(client.listForCustomer(req.params.id));
});

app.post("/orders", (req, res) => {
  res.status(201).json({ received: true });
});

// The course's lesson 4 source (reproduced above) exports `app` and stops
// there — it's read and edited by Cursor, and imported directly by the
// tests, neither of which needs a bound port. Actually running the service
// with `npm run dev` needs a `.listen()` call, which the lesson never shows
// because it never boots the server on the page. Added here, gated so
// importing this module (as the test suite does) still has no side effect.
if (require.main === module) {
  const port = process.env.PORT ? Number(process.env.PORT) : 3000;
  app.listen(port, () => {
    console.log(`order-api listening on http://localhost:${port}`);
  });
}

export default app;
