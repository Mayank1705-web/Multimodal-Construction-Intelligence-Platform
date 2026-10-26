export default function Architecture() {
  return (
    <>
      <div className="page-head">
        <h1>System architecture</h1>
        <p>The React frontend sends text, images and project data to the FastAPI backend. The backend calls the multimodal model, validates every reply against a strict JSON schema, and stores results.</p>
      </div>
      <img className="arch-img" src="/architecture.png" alt="Architecture diagram: the platform receives user input, processes it with a multimodal AI, and generates safety monitoring, crack analysis, valuation, project planning and daily site assistance outputs. The FastAPI backend stores and retrieves data." />
    </>
  );
}
