class RateLimiter
  attr_reader :requests

  def initialize(max_requests = 100, window_seconds = 60)
    @max_requests = max_requests
    @window_seconds = window_seconds
    @requests = Hash.new { |h, k| h[k] = [] }
  end

  def allow?(client_id)
    now = Time.now
    cleanup_old_requests(client_id, now)

    if @requests[client_id].size < @max_requests
      @requests[client_id] << now
      true
    else
      false
    end
  end

  def remaining_requests(client_id)
    cleanup_old_requests(client_id, Time.now)
    @max_requests - @requests[client_id].size
  end

  def reset_time(client_id)
    return Time.now if @requests[client_id].empty?

    oldest_request = @requests[client_id].first
    oldest_request + @window_seconds
  end

  def reset_client(client_id)
    @requests.delete(client_id)
  end

  private

  def cleanup_old_requests(client_id, current_time)
    cutoff_time = current_time - @window_seconds
    @requests[client_id].reject! { |timestamp| timestamp < cutoff_time }
  end
end
