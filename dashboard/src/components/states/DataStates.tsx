export function LoadingState() {
  return (
    <div className="state-message" role="status" aria-live="polite">
      <span className="loading-indicator" aria-hidden="true" />
      <div>
        <h2>Loading trial data</h2>
        <p>Reading the analysis bundle.</p>
      </div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state-message state-message-error" role="alert">
      <div>
        <h2>Data could not be loaded</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}

export function EmptyState({
  message = "No samples match these filters.",
  onClear,
}: {
  message?: string;
  onClear?: () => void;
}) {
  return (
    <div className="state-message">
      <div>
        <h2>No data to show</h2>
        <p>{message}</p>
        {onClear ? (
          <button className="text-button" type="button" onClick={onClear}>
            Clear filters
          </button>
        ) : null}
      </div>
    </div>
  );
}
