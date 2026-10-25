# Focused revision — Python, SQL, APIs

Tumhe yeh topics aate hain. Pehle short diagnostic karo; jo confidently explain/build ho jaye usko fast-track karo. Revision RAG project ke actual code ke saath hogi.

| Topic | Revision check | RAG mein application |
| --- | --- | --- |
| Python typing + validation | External payload ko typed model mein validate karo; invalid field ka expected behavior explain karo | Upload config, retrieval settings, provider responses |
| Async + processes | Network wait vs CPU-heavy parsing ka execution explain karo; cancellation ka effect predict karo | Embedding API calls, parsing worker, stream disconnect |
| SQL joins + authorization | Membership se accessible KB/documents query derive karo; cross-org input reject explain karo | Search, history, source fetch isolation |
| Transactions + constraints | Same operation twice execute hone par uniqueness/rollback behavior explain karo | Ingestion idempotency and active version publication |
| Indexes + query plans | Filtered query ka plan read karo; index used hai ya nahi identify karo | Full-text/vector performance experiments |
| HTTP + streaming | Upload acceptance vs job completion, error status aur partial stream failure distinguish karo | Background ingestion and chat SSE |
| Docker + configuration | API, DB, Redis aur worker lifecycle explain karo; persistent volume ka role batao | Reproducible local pipeline and restart recovery |

Suggested diagnostic: small API request se authorized DB read tak trace banao; worker retry aur transaction failure ke outcomes explain karo. Yeh diagnostic abhi run nahi hua; familiarity ko verified mastery mark nahi karenge.

Revision ke baad first practical target: known source spans wale TXT/Markdown corpus par inspectable lexical retrieval aur initial evaluation report. Advanced sequence [modern RAG labs](06-modern-rag.md) mein hai.
