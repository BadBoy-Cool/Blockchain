class SmartContract:
    def __init__(self):
        self.standard_workdays = 22  # Số ngày công chuẩn trong tháng
        self.overtime_rate = 1.5    # Hệ số tăng ca
        self.max_bonus = 1000       # Thưởng KPI tối đa (USD)

    def calculate_base_salary(self, agreed_salary, actual_workdays):
        return agreed_salary * (actual_workdays / self.standard_workdays)

    def calculate_overtime_salary(self, overtime_hours, agreed_salary):
        hourly_rate = agreed_salary / (self.standard_workdays * 8)  # 8 giờ/ngày
        return overtime_hours * hourly_rate * self.overtime_rate

    def calculate_kpi_bonus(self, kpi_score):
        return self.max_bonus * (kpi_score / 100)

    def calculate_total_salary(self, base_salary, overtime_salary, kpi_bonus, deductions=0):
        return base_salary + overtime_salary + kpi_bonus - deductions