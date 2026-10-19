import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import ReviewForm from "./components/ReviewForm";

test("lets users choose queued processing when enabled by the server", () => {
  const onSubmit = jest.fn();

  function ReviewFormHarness() {
    const [useQueue, setUseQueue] = useState(true);
    return (
      <ReviewForm
        onSubmit={onSubmit}
        loading={false}
        queueEnabled
        useQueue={useQueue}
        onQueueChange={setUseQueue}
        rateLimitingEnabled={false}
      />
    );
  }

  render(<ReviewFormHarness />);

  const queueSwitch = screen.getByRole("checkbox", {
    name: /use background worker/i,
  });
  expect(queueSwitch).toBeChecked();
  expect(screen.getByText(/api rate limiting: off/i)).toBeInTheDocument();

  fireEvent.click(queueSwitch);
  expect(queueSwitch).not.toBeChecked();

  fireEvent.change(screen.getByPlaceholderText(/github.com\/owner\/repo\/pull/i), {
    target: { value: "https://github.com/owner/repo/pull/123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
  expect(onSubmit).toHaveBeenCalledWith(
    "https://github.com/owner/repo/pull/123",
    false,
    false,
  );
});

test("disables queued mode when the backend has disabled Celery", () => {
  render(
    <ReviewForm
      onSubmit={jest.fn()}
      loading={false}
      queueEnabled={false}
      useQueue={false}
      onQueueChange={jest.fn()}
      rateLimitingEnabled
    />,
  );

  expect(
    screen.getByRole("checkbox", { name: /use background worker/i }),
  ).toBeDisabled();
  expect(screen.getByText(/disabled by server/i)).toBeInTheDocument();
  expect(screen.getByText(/api rate limiting: on/i)).toBeInTheDocument();
});
