require 'time'

class RequestLogger
  attr_reader :logs

  def initialize
    @logs = []
  end

  def log_request(method, path, status, duration)
    entry = {
      method: method,
      path: path,
      status: status,
      duration_ms: duration,
      timestamp: Time.now
    }
    @logs << entry
  end

  def get_logs(limit = 100)
    @logs.last(limit)
  end

  def get_error_logs
    @logs.select { |log| log[:status] >= 400 }
  end

  def get_average_response_time
    return 0.0 if @logs.empty?

    total_time = @logs.sum { |log| log[:duration_ms] }
    total_time.to_f / @logs.size
  end

  def clear_logs
    @logs.clear
  end
end
