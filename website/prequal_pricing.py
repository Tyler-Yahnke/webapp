from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Spreads, PrimeRate
import datetime
from sqlalchemy import desc, and_

prequal_pricing = Blueprint('prequal_pricing', __name__)


@prequal_pricing.route('/', methods=['GET', 'POST'])
@login_required
def pricing_model_func():
    global userselection_product, legalFees, product, plOrCl, terms, amortTerms, loanAmount, interestRate, gracePeriod, borrowerExperience, downPaymentPercent, brandCategory, gdscr, operatorExperience, fico, pcr, nbrOfAows, equipmentGuarantee, guarantee, useOfFunds, monthsSinceBreakeven, franchisorExperience, fccr, fccrBasis, intelliscore

    results = {
        'investmentGrade': '',
        'investmentGrade': '',
        'downPaymentMultiplier': '',
        'unitFailureMultiplier': '',
        'gdscrMultiplier': '',
        'operatorExperienceMultiplier': '',
        'personalCreditMultiplier': '',
        'pcrMultiplier': '',
        'loanPurposeMultiplier': '',
        'timeInBusinessMultiplier': '',
        'franchsiorExperienceMultiplier': '',
        'fccrMultiplier': '',
        'intelliscoreMultiplier': '',
        'riskFlagMultiplier': '',
        'finalFailureRate': '',
        'cumulativeNetLossRate': '',
        'annualNetLossRate': ''
    }

    previous_data = {}

    button = request.form.get('clear')
    if button == 'Clear':
        results = {
            'investmentGrade': '',
            'investmentGrade':'',
            'downPaymentMultiplier':'',
            'unitFailureMultiplier':'',
            'gdscrMultiplier':'',
            'operatorExperienceMultiplier':'',
            'personalCreditMultiplier':'',
            'pcrMultiplier':'',
            'loanPurposeMultiplier':'',
            'timeInBusinessMultiplier':'',
            'franchsiorExperienceMultiplier':'',
            'fccrMultiplier':'',
            'intelliscoreMultiplier':'',
            'riskFlagMultiplier':'',
            'finalFailureRate':'',
            'cumulativeNetLossRate':'',
            'annualNetLossRate':''
        }

        return render_template("prequal_pricing_model.html", user=current_user, results=results, previous_data=previous_data)

    else:

        pass

    if request.method == 'POST':
        previous_data = {
            'product' : request.form.get('product'),
            'plOrCl' : request.form.get('plOrCl'),

            'corpGuarantor': request.form.get('corpGuarantor'),
            'newterms' : request.form.get('newterms'),
            'newamortTerms' : request.form.get('newamortTerms'),
            'newloanAmount' : request.form.get('newloanAmount'),
            'newbrandCategory' : request.form.get('newbrandCategory'),
            'newfico' : request.form.get('newfico'),
            'newpcr' : request.form.get('newpcr'),
            'newgracePeriod' : request.form.get('newgracePeriod'),
            'newborrowerExperience' : request.form.get('newborrowerExperience'),
            'newdownPaymentPercent' : request.form.get('newdownPaymentPercent'),
            'newgdscr' : request.form.get('newgdscr'),
            'newoperatorExperience' : request.form.get('newoperatorExperience'),

            'recapterms' : request.form.get('recapterms'),
            'recapamortTerms' : request.form.get('recapamortTerms'),
            'recaploanAmount' : request.form.get('recaploanAmount'),
            'recapbrandCategory' : request.form.get('recapbrandCategory'),
            'recapfico' : request.form.get('recapfico'),
            'recappcr' : request.form.get('recappcr'),
            'recapuseOfFunds' : request.form.get('recapuseOfFunds'),
            'recapmonthsSinceBreakeven' : request.form.get('recapmonthsSinceBreakeven'),
            'recapfranchisorExperience' : request.form.get('recapfranchisorExperience'),
            'recapfccr' : request.form.get('recapfccr'),
            'recapfccrBasis' : request.form.get('recapfccrBasis'),
            'recapintelliscore' : request.form.get('recapintelliscore'),

            'purchaseterms' : request.form.get('purchaseterms'),
            'purchaseamortTerms' : request.form.get('purchaseamortTerms'),
            'purchaseloanAmount' : request.form.get('purchaseloanAmount'),
            'purchasebrandCategory' : request.form.get('purchasebrandCategory'),
            'purchasefico' : request.form.get('purchasefico'),
            'purchasepcr' : request.form.get('purchasepcr'),
            'purchaseborrowerExperience' : request.form.get('purchaseborrowerExperience'),
            'purchasedownPaymentPercent' : request.form.get('purchasedownPaymentPercent'),
            'purchaseoperatorExperience' : request.form.get('purchaseoperatorExperience'),
            'purchasemonthsSinceBreakeven' : request.form.get('purchasemonthsSinceBreakeven'),
            'purchasefccr' : request.form.get('purchasefccr'),
            'purchasefccrBasis' : request.form.get('purchasefccrBasis'),
            'purchaseintelliscore': request.form.get('purchaseintelliscore'),

            'nbrOfAows': request.form.get('nbrOfAows'),
            'equipmentGuarantee': request.form.get('equipmentGuarantee'),
            'guarantee': request.form.get('guarantee')
        }



        missing_selection = missing()
        if missing_selection == 'Missing':
            return render_template("prequal_pricing_model.html", user=current_user, results=results, previous_data=previous_data)
        else:
            pass

        #common inputs for all types
        userselection_product = request.form.get('product')
        plOrCl = request.form.get('plOrCl')
        legalFees = 10000


        if userselection_product == 'New Unit' and plOrCl =='Proposal':
            print('new/proposal')

            #need to figure out the 7 vs 10
            terms = int(request.form.get('newterms'))
            amortTerms = int(request.form.get('newamortTerms'))
            if terms == amortTerms:
                product = 'New_7'
            else:
                product = 'New_10'

            loanAmount = int(request.form.get('newloanAmount'))
            brandCategory = request.form.get('newbrandCategory')
            fico = int(request.form.get('newfico'))
            pcr = float(request.form.get('newpcr'))
            gracePeriod = int(request.form.get('newgracePeriod'))
            borrowerExperience = request.form.get('newborrowerExperience')
            downPaymentPercent = float(request.form.get('newdownPaymentPercent'))
            gdscr = float(request.form.get('newgdscr'))
            operatorExperience = request.form.get('newoperatorExperience')
            nbrOfAows = int(0)
            equipmentGuarantee = 0
            guarantee = 0

            validation_rules = validations()

            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()

            new()
            results = fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        elif userselection_product == 'New Unit' and plOrCl =='Commitment':
            print('new/commitment')

            # need to figure out the 7 vs 10
            terms = int(request.form.get('newterms'))
            amortTerms = int(request.form.get('newamortTerms'))
            if terms == amortTerms:
                product = 'New_7'
            else:
                product = 'New_10'

            loanAmount = int(request.form.get('newloanAmount'))
            brandCategory = request.form.get('newbrandCategory')
            fico = int(request.form.get('newfico'))
            pcr = float(request.form.get('newpcr'))
            gracePeriod = int(request.form.get('newgracePeriod'))
            borrowerExperience = request.form.get('newborrowerExperience')
            downPaymentPercent = float(request.form.get('newdownPaymentPercent'))
            gdscr = float(request.form.get('newgdscr'))
            operatorExperience = request.form.get('newoperatorExperience')
            nbrOfAows = int(request.form.get('nbrOfAows'))
            equipmentGuarantee = float(request.form.get('equipmentGuarantee'))
            guarantee = float(request.form.get('guarantee'))

            validation_rules = validations()

            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()

            new()
            results = fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        elif userselection_product == 'Recap' and plOrCl =='Proposal':
            print('recap/proposal')

            # need to figure out the 7 vs 10
            terms = int(request.form.get('recapterms'))
            amortTerms = int(request.form.get('recapamortTerms'))
            if terms == amortTerms:
                product = 'Recap_7'
            else:
                product = 'Recap_10'

            loanAmount = int(request.form.get('recaploanAmount'))
            brandCategory = request.form.get('recapbrandCategory')
            fico = int(request.form.get('recapfico'))
            pcr = float(request.form.get('recappcr'))
            useOfFunds = request.form.get('recapuseOfFunds')
            monthsSinceBreakeven = int(request.form.get('recapmonthsSinceBreakeven'))
            franchisorExperience = request.form.get('recapfranchisorExperience')
            fccr = float(request.form.get('recapfccr'))
            fccrBasis = request.form.get('recapfccrBasis')
            intelliscore = request.form.get('recapintelliscore')
            gracePeriod = int(0)
            nbrOfAows = int(0)
            equipmentGuarantee = 0
            guarantee = 0

            validation_rules = validations()

            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()

            recap()
            results = fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        elif userselection_product == 'Recap' and plOrCl =='Commitment':
            print('recap/commitment')

            # need to figure out the 7 vs 10
            terms = int(request.form.get('recapterms'))
            amortTerms = int(request.form.get('recapamortTerms'))
            if terms == amortTerms:
                product = 'Recap_7'
                print('recap7')
            else:
                product = 'Recap_10'
                print('recap10')

            loanAmount = int(request.form.get('recaploanAmount'))
            brandCategory = request.form.get('recapbrandCategory')
            fico = int(request.form.get('recapfico'))
            pcr = float(request.form.get('recappcr'))
            useOfFunds = request.form.get('recapuseOfFunds')
            monthsSinceBreakeven = int(request.form.get('recapmonthsSinceBreakeven'))
            franchisorExperience = request.form.get('recapfranchisorExperience')
            fccr = float(request.form.get('recapfccr'))
            fccrBasis = request.form.get('recapfccrBasis')
            intelliscore = request.form.get('recapintelliscore')
            nbrOfAows = int(request.form.get('nbrOfAows'))
            equipmentGuarantee = float(request.form.get('equipmentGuarantee'))
            guarantee = float(request.form.get('guarantee'))
            gracePeriod = int(0)

            validation_rules = validations()
            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()

            recap()
            results = fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        elif userselection_product == 'Purchase' and plOrCl =='Proposal':
            print('purchase/proposal')

            # need to figure out the 7 vs 10
            terms = int(request.form.get('purchaseterms'))
            amortTerms = int(request.form.get('purchaseamortTerms'))
            if terms == amortTerms:
                product = 'Purchase_7'
                print('purchase7')
            else:
                product = 'Purchase_10'
                print('purchase10')

            loanAmount = int(request.form.get('purchaseloanAmount'))
            brandCategory = request.form.get('purchasebrandCategory')
            fico = int(request.form.get('purchasefico'))
            pcr = float(request.form.get('purchasepcr'))
            borrowerExperience = request.form.get('purchaseborrowerExperience')
            downPaymentPercent = float(request.form.get('purchasedownPaymentPercent'))
            operatorExperience = request.form.get('purchaseoperatorExperience')
            monthsSinceBreakeven = int(request.form.get('purchasemonthsSinceBreakeven'))
            fccr = float(request.form.get('purchasefccr'))
            fccrBasis = request.form.get('purchasefccrBasis')
            intelliscore = request.form.get('purchaseintelliscore')
            nbrOfAows = int(0)
            equipmentGuarantee = 0
            guarantee = 0
            gracePeriod = int(0)

            validation_rules = validations()

            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()

            purchase()
            results = fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        elif userselection_product == 'Purchase' and plOrCl =='Commitment':
            print('purchase/commitment')

            # need to figure out the 7 vs 10
            terms = int(request.form.get('purchaseterms'))
            amortTerms = int(request.form.get('purchaseamortTerms'))
            if terms == amortTerms:
                product = 'Purchase_7'
            else:
                product = 'Purchase_10'

            loanAmount = int(request.form.get('purchaseloanAmount'))
            brandCategory = request.form.get('purchasebrandCategory')
            fico = int(request.form.get('purchasefico'))
            pcr = float(request.form.get('purchasepcr'))
            borrowerExperience = request.form.get('purchaseborrowerExperience')
            downPaymentPercent = float(request.form.get('purchasedownPaymentPercent'))
            operatorExperience = request.form.get('purchaseoperatorExperience')
            monthsSinceBreakeven = int(request.form.get('purchasemonthsSinceBreakeven'))
            fccr = float(request.form.get('purchasefccr'))
            fccrBasis = request.form.get('purchasefccrBasis')
            intelliscore = request.form.get('purchaseintelliscore')
            nbrOfAows = int(request.form.get('nbrOfAows'))
            equipmentGuarantee = float(request.form.get('equipmentGuarantee'))
            guarantee = float(request.form.get('guarantee'))
            gracePeriod = int(0)

            validation_rules = validations()

            if validation_rules == 'Fail':
                return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)
            else:
                pass

            get_interest_rate()
            purchase()
            results=fields

            return render_template("prequal_pricing_model.html", user=current_user, results=results,previous_data=previous_data)

        else:
            print('missed')
            pass

        return render_template("prequal_pricing_model.html", user=current_user,results=results, previous_data=previous_data)

    return render_template("prequal_pricing_model.html", user=current_user, results=results, previous_data=previous_data)


def missing():
    userselection_product = request.form.get('product')
    plOrCl = request.form.get('plOrCl')

    if userselection_product== 'Make Selection' or plOrCl == 'Make Selection':
        flash('Missing Product or Proposal/Commitment', category='error')
        return 'Missing'

    elif plOrCl == 'Commitment':
        nbrOfAows = request.form.get('nbrOfAows')
        guarantee = request.form.get('guarantee')
        equipmentGuarantee = request.form.get('equipmentGuarantee')
        if nbrOfAows == 'Make Selection':
            flash('Missing Number of AOWs', category='error')
            return 'Missing'
        elif equipmentGuarantee == '':
            flash('Missing Equipment Guarantee', category='error')
            return 'Missing'
        elif guarantee == '':
            flash('Missing Guarantee', category='error')
            return 'Missing'

    elif userselection_product == 'New Unit':
        terms = request.form.get('newterms')
        amortTerms = request.form.get('newamortTerms')
        loanAmount = request.form.get('newloanAmount')
        brandCategory = request.form.get('newbrandCategory')
        fico = request.form.get('newfico')
        pcr = request.form.get('newpcr')
        gracePeriod = request.form.get('newgracePeriod')
        borrowerExperience = request.form.get('newborrowerExperience')
        downPaymentPercent = request.form.get('newdownPaymentPercent')
        gdscr = request.form.get('newgdscr')
        operatorExperience = request.form.get('newoperatorExperience')

        if terms == 'Make Selection' or amortTerms == 'Make Selection' or borrowerExperience == 'Make Selection' or brandCategory=='Make Selection':
            flash('Missing Input: Make Selection', category='error')
            return 'Missing'
        elif loanAmount=='' or fico=='' or pcr=='' or gracePeriod=='' or downPaymentPercent =='' or gdscr=='' or operatorExperience=='':
            flash('Missing Input: Input is Blank', category='error')
            return 'Missing'


    elif userselection_product == 'Recap':
        terms = request.form.get('recapterms')
        amortTerms = request.form.get('recapamortTerms')
        loanAmount = request.form.get('recaploanAmount')
        brandCategory = request.form.get('recapbrandCategory')
        fico = request.form.get('recapfico')
        pcr = request.form.get('recappcr')
        useOfFunds = request.form.get('recapuseOfFunds')
        monthsSinceBreakeven = request.form.get('recapmonthsSinceBreakeven')
        franchisorExperience = request.form.get('recapfranchisorExperience')
        fccr = request.form.get('recapfccr')
        fccrBasis = request.form.get('recapfccrBasis')
        intelliscore = request.form.get('recapintelliscore')

        if terms == 'Make Selection' or amortTerms == 'Make Selection' or brandCategory== 'Make Selection' or useOfFunds=='Make Selection' or franchisorExperience=='Make Selection' or fccrBasis=='Make Selection' or intelliscore=='Make Selection':
            flash('Missing Input: Make Selection', category='error')
            return 'Missing'
        elif loanAmount=='' or fico=='' or pcr=='' or monthsSinceBreakeven=='' or fccr=='':
            flash('Missing Input: Input is Blank', category='error')
            return 'Missing'


    elif userselection_product == 'Purchase':
        terms = request.form.get('purchaseterms')
        amortTerms = request.form.get('purchaseamortTerms')
        loanAmount = request.form.get('purchaseloanAmount')
        brandCategory = request.form.get('purchasebrandCategory')
        fico = request.form.get('purchasefico')
        pcr = request.form.get('purchasepcr')
        borrowerExperience = request.form.get('purchaseborrowerExperience')
        downPaymentPercent = request.form.get('purchasedownPaymentPercent')
        operatorExperience = request.form.get('purchaseoperatorExperience')
        monthsSinceBreakeven = request.form.get('purchasemonthsSinceBreakeven')
        fccr = request.form.get('purchasefccr')
        fccrBasis = request.form.get('purchasefccrBasis')
        intelliscore = request.form.get('purchaseintelliscore')
        if terms == 'Make Selection' or amortTerms == 'Make Selection' or borrowerExperience == 'Make Selection' or brandCategory=='Make Selection' or fccrBasis=='Make Selection' or intelliscore=='Make Selection':
            flash('Missing Input: Make Selection', category='error')
            return 'Missing'
        elif loanAmount=='' or fico=='' or pcr=='' or downPaymentPercent =='' or operatorExperience=='' or monthsSinceBreakeven=='' or fccr=='':
            flash('Missing Input: Input is Blank', category='error')
            return 'Missing'

    else:
        return None

def validations():
    valid_options = ['60/60', '60/84', '84/84', '84/120', '120/120']
    option = f"{terms}/{amortTerms}"
    if option not in valid_options:
        flash('Invalid Term/Amortization', category='error')
        return 'Fail'
    elif loanAmount < float('100000') or loanAmount > float('600000'):
        flash('Invalid Loan Amount', category='error')
        return 'Fail'
    elif gracePeriod < 0 or gracePeriod >12:
        flash('Invalid Grace Period', category='error')
        return 'Fail'
    elif fico < 300 or fico >850:
        flash('Invalid FICO', category='error')
        return 'Fail'
    elif pcr < 0 or pcr > 999:
        flash('Invalid PCR', category='error')
        return 'Fail'

    elif userselection_product != 'Recap':
        if downPaymentPercent < 0 or downPaymentPercent >100:
            flash('Invalid Down Payment Percentage', category='error')
            return 'Fail'

    elif userselection_product == 'New Unit':
        print('here')
        if int(gdscr) < 0 or int(gdscr) >999:
            flash('Invalid GDSCR', category='error')
            return 'Fail'

    elif userselection_product == 'Recap':
        if fccr < 0 or fccr >999:
            flash('Invalid FCCR', category='error')
            return 'Fail'

    else:
        return None

def get_interest_rate():
    global interestRate
    # Getting Interest Rate
    today = datetime.datetime.today()
    userselection_term = f"term_{terms}_{amortTerms}"
    corpGuarantor = request.form.get('corpGuarantor')
    if userselection_product == 'New Unit' and corpGuarantor== None:
        pricingBasis = 'Pro Forma'

    else:
        pricingBasis = 'Cash Flow'

    selected_spread = Spreads.query.filter(
        and_(
            Spreads.Start <= today,
            Spreads.End >= today,
            Spreads.APCGrade == 'A',
            Spreads.PricingBasis == pricingBasis,
            Spreads.RateType == 'Fixed'
        )
    ).first()
    spread_rate = float(getattr(selected_spread, userselection_term))

    prime_rate = PrimeRate.query.order_by(desc(PrimeRate.Date)).first()

    interestRate = float(prime_rate.Rate) + float(spread_rate)

    return interestRate



# ## Start: Function creation for Pricing Model

# ### Below functions will not vary

def gdscr_multiplier(gdscr):
    if gdscr < 1.6:
        return 5
    elif gdscr < 1.65:
        return 1.6
    elif gdscr < 1.7:
        return 1.5
    elif gdscr < 1.8:
        return 1.4
    elif gdscr < 1.9:
        return 1.3
    elif gdscr <= 2:
        return 1.15
    elif gdscr < 2.09:
        return 1
    elif gdscr < 3:
        return 0.95
    else:
        return 0.85

def borrower_exp_multiplier(operator_exp):
    if operator_exp == 'New/New':
        return 1.35
    elif operator_exp == 'New/Experienced - General biz/other brands':
        return 1
    elif operator_exp == 'New/Experienced - Single unit this brand':
        return 0.85
    elif operator_exp == 'New/Experienced - Multi units this brand':
        return 0.75
    else:
        return 5

def personal_credit_multiplier(fico):
    if fico > 850:
        return 5
    elif fico > 780:
        return 0.9
    elif fico > 720:
        return 1
    elif fico > 700:
        return 1.1
    elif fico > 680:
        return 1.2
    elif fico > 660:
        return 1.3
    elif fico == 0:
        return 1
    else:
        return 1.4

def risk_flag_multiplier(aows):
    if aows < 2:
        return 1
    elif aows == 2:
        return 1.1
    elif aows == 3:
        return 1.5
    else:
        return 5

def monthly_gross_loss_func(monthly_balance_array, monthly_loss_rate_array):
    monthly_gross_loss_array = [0]

    for month in range(1, 85):
        monthly_gross_loss_array.append(round(monthly_balance_array[month] * monthly_loss_rate_array[month], 2))

    return monthly_gross_loss_array

def monthly_asset_deprec_func(equipment_guarantee):
    monthly_asset_deprec_array = [equipment_guarantee]

    for month in range(1, 85):
        if month <= 6:
            monthly_asset_deprec_array.append(equipment_guarantee * 0.75)
        elif month <= 18:
            monthly_asset_deprec_array.append(equipment_guarantee * 0.5)
        elif month <= 30:
            monthly_asset_deprec_array.append(equipment_guarantee * 0.25)
        elif month <= 36:
            monthly_asset_deprec_array.append(equipment_guarantee * 0.1)
        else:
            monthly_asset_deprec_array.append(0)
    return monthly_asset_deprec_array

def monthly_net_loss_func(monthly_gross_loss_array, monthly_recovery_array):
    monthly_net_loss_array = list()

    for month in range(85):
        monthly_net_loss_array.append(round(monthly_gross_loss_array[month] - monthly_recovery_array[month], 8))
    return monthly_net_loss_array

def total_loss(monthly_net_loss_array):
    return round(sum(monthly_net_loss_array), 2)

def monthly_portfolio_balance_func(monthly_open_acct_array, monthly_balance_array):
    monthly_port_bal_array = list()

    for month in range(1, 85):
        monthly_port_bal_array.append(round(monthly_balance_array[month] * monthly_open_acct_array[month], 2))

    return monthly_port_bal_array

def avg_portfolio_balance(monthly_portfolio_balance_array):
    return round(sum(monthly_portfolio_balance_array) / 84, 2)

def cuml_net_loss_rate(total_net_loss, avg_port_bal):
    return round(total_net_loss / avg_port_bal, 10)

def annl_net_loss_rate(cumulative_loss_rate):
    return round(cumulative_loss_rate / 7, 8)

def investment_grade(annl_loss_rate):
    if annl_loss_rate <= 0.6 / 100:
        return 'AA'
    elif annl_loss_rate <= 0.8 / 100:
        return 'A'
    elif annl_loss_rate <= 1 / 100:
        return 'B'
    elif annl_loss_rate <= 1.2 / 100:
        return 'C'
    elif annl_loss_rate <= 1.4 / 100:
        return 'D'
    elif annl_loss_rate <= 1.6 / 100:
        return 'E'
    elif annl_loss_rate <= 1.74:
        return 'HR2'
    else:
        return 'FAIL'

def loan_purpose_multiplier(use_of_funds):
    if use_of_funds == 'Cash Out (Cash, WC, small loans > 25% of loan amount)':
        return 1.25
    elif use_of_funds == 'Cash Out (Cash, WC, small loans < 25% of loan amount)':
        return 1.15
    elif use_of_funds == 'Refinance to free up assets':
        return 1.1
    elif use_of_funds == 'Recap to fund additional unit/growth':
        return 1
    elif use_of_funds == 'Debt consolidation':
        return 1
    elif use_of_funds == 'Refi to cheaper rate (not from high risk lending)':
        return 0.9
    elif use_of_funds == 'Remodel or relocation':
        return 0.8
    else:
        return 5

def time_in_biz_multiplier(months_to_breakeven):
    if months_to_breakeven > 61:
        return 0.8
    elif months_to_breakeven >= 36:
        return 0.9
    elif months_to_breakeven >= 19:
        return 1
    elif months_to_breakeven >= 1:
        return 1.05
    else:
        return 1.25

def franchisor_exp_multiplier(franchisor_exp):
    if franchisor_exp == '1 unit/<2 years franchising':
        return 1.1
    elif franchisor_exp == '1 unit/2 years franchising':
        return 1
    elif franchisor_exp == '1 unit/3 years franchising':
        return 0.95
    elif franchisor_exp == '1 unit/5 years franchising':
        return 0.9
    elif franchisor_exp == '2 units/3  years franchising':
        return 0.85
    elif franchisor_exp == '3 units/3 years franchising':
        return 0.8
    elif franchisor_exp == '5 units/5 years franchising':
        return 0.75
    elif franchisor_exp == 'Previous successful loan with APC (requires validation of financials)':
        return 0.75
    else:
        return 5

def fccr_multiplier(fccr, fccr_basis):
    if fccr_basis == 'Based on Tax Returns':
        if fccr <= 1.2:
            return 1.5
        elif fccr <= 1.249:
            return 1.3
        elif fccr <= 1.29:
            return 1.2
        elif fccr <= 1.39:
            return 1.1
        elif fccr <= 1.49:
            return 1.0
        elif fccr <= 1.64:
            return 0.9
        elif fccr <= 1.99:
            return 0.8
        elif fccr <= 2.99:
            return 0.7
        else:
            return 0.60
    elif fccr_basis == 'Based on Other':
        if fccr <= 1.2:
            return 1.5
        elif fccr <= 1.249:
            return 1.4
        elif fccr <= 1.29:
            return 1.3
        elif fccr <= 1.39:
            return 1.2
        elif fccr <= 1.49:
            return 1.1
        elif fccr <= 1.64:
            return 1
        elif fccr <= 1.99:
            return 0.9
        elif fccr <= 2.99:
            return 0.75
        else:
            return 0.60
    else:
        return 5

def intelliscore_multiplier(intelliscore):
    if intelliscore == 'High Risk':
        return 1.25
    elif intelliscore == 'High/Med Risk':
        return 1.15
    elif intelliscore == 'Med Risk':
        return 1
    elif intelliscore == 'Low/Med Risk':
        return 0.9
    elif intelliscore == 'Low Risk':
        return 0.8
    elif intelliscore == 'No Score':
        return 1.05
    else:
        return 5

# ### Below functions vary by product type

def monthly_payment(product, amount, rate, terms, interest_only):
    if product in ('New_7', 'New_10'):
        intrate = float(rate) / 12.0
        totalpmts = float(terms) - float(interest_only)
        payment = (intrate * amount) / (1 - pow(1 + intrate, -totalpmts))
        return round(payment, 2)
    else:
        intrate = rate / 12.0
        totalpmts = terms
        payment = (intrate * amount) / (1 - pow(1 + intrate, -totalpmts))
        return round(payment, 2)

def monthly_balance_func(product, loan_amount, interest_rate, amort_terms, interest_only):
    if product in ('New_7', 'New_10'):
        monthly_payment_val = monthly_payment(product, loan_amount, interest_rate, amort_terms, interest_only)
        recursive_loan_amount = round(loan_amount, 2)
        recursive_interest_payment = round((loan_amount * interest_rate) / 12, 2)

        balance_array = [recursive_loan_amount]
        interest_payment_array = [recursive_interest_payment]

        for month in range(1, 85):

            if month <= interest_only:
                balance_array.append(recursive_loan_amount)
                interest_payment_array.append(round((recursive_loan_amount * interest_rate) / 12, 2))

            else:

                balance_array.append(recursive_loan_amount)

                recursive_interest_payment = round((recursive_loan_amount * interest_rate) / 12, 2)
                interest_payment_array.append(recursive_interest_payment)

                recursive_loan_amount = round(recursive_loan_amount + recursive_interest_payment - monthly_payment_val,
                                              2)

        return balance_array

    else:
        monthly_payment_val = monthly_payment(product, loan_amount, interest_rate, amort_terms, interest_only)
        recursive_loan_amount = round(loan_amount, 2)
        recursive_interest_payment = round((loan_amount * interest_rate) / 12, 2)

        balance_array = [recursive_loan_amount]
        interest_payment_array = [recursive_interest_payment]

        for month in range(1, 85):
            balance_array.append(recursive_loan_amount)

            recursive_interest_payment = round((recursive_loan_amount * interest_rate) / 12, 2)
            interest_payment_array.append(recursive_interest_payment)

            recursive_loan_amount = round(recursive_loan_amount + recursive_interest_payment - monthly_payment_val, 2)

        return balance_array

def down_payment_multiplier(product, borrower_exp, down_payment_percent):
    if product in ('New_7', 'New_10'):
        if borrower_exp == 'N/N':
            if down_payment_percent < 15:
                return 5
            elif down_payment_percent < 20:
                return 1.35
            elif down_payment_percent < 25:
                return 1.25
            elif down_payment_percent < 27.5:
                return 1.1
            elif down_payment_percent < 33:
                return 1
            elif down_payment_percent < 40:
                return 0.9
            elif down_payment_percent < 50:
                return 0.8
            else:
                return 0.7

        elif borrower_exp == 'Exp':
            if down_payment_percent < 15:
                return 5
            elif down_payment_percent < 20:
                return 1.15
            elif down_payment_percent < 25:
                return 1.10
            elif down_payment_percent < 27.5:
                return 1
            elif down_payment_percent < 33:
                return 0.9
            elif down_payment_percent < 40:
                return 0.8
            elif down_payment_percent < 50:
                return 0.7
            else:
                return 0.6

        else:
            return 5

    elif product in ('Purchase_7', 'Purchase_10'):
        if borrower_exp == 'Inexp':
            if down_payment_percent < 15:
                return 5
            elif down_payment_percent < 20:
                return 1.35
            elif down_payment_percent < 25:
                return 1.25
            elif down_payment_percent < 27.5:
                return 1.1
            elif down_payment_percent < 33:
                return 1
            elif down_payment_percent < 40:
                return 0.9
            elif down_payment_percent < 50:
                return 0.8
            else:
                return 0.7

        elif borrower_exp == 'Exp':
            if down_payment_percent < 15:
                return 5
            elif down_payment_percent < 20:
                return 1.15
            elif down_payment_percent < 25:
                return 1.10
            elif down_payment_percent < 27.5:
                return 1
            elif down_payment_percent < 33:
                return 0.9
            elif down_payment_percent < 40:
                return 0.8
            elif down_payment_percent < 50:
                return 0.7
            else:
                return 0.6

        else:
            return 5

def brand_unit_failure_multiplier(product, brand_category):
    if product in ('New_10', 'New_7'):
        if brand_category == 'Category 1':
            return 0.02
        elif brand_category == 'Category 2':
            return 0.04
        else:
            return 5

    elif product in ('Recap_7', 'Recap_10', 'Purchase_7', 'Purchase_10'):
        if brand_category == 'Category 1':
            return 0.01
        elif brand_category == 'Category 2':
            return 0.013
        elif brand_category == 'Category 3':
            return 0.016
        else:
            return 5

    else:
        return 5

def pcr_multiplier(product, pcr):
    if product in ('New_7', 'New_10'):
        if pcr <= 0.75:
            return 1.75
        elif pcr < 1:
            return 1.5
        elif pcr <= 1.24:
            return 1.35
        elif pcr < 1.5:
            return 1.2
        elif pcr <= 2:
            return 1.1
        elif pcr < 3:
            return 1
        elif pcr < 7:
            return 0.85
        elif pcr < 10:
            return 0.7
        else:
            return 0.6

    elif product in ('Recap_7', 'Recap_10'):
        if pcr <= 0.5:
            return 1.25
        elif pcr <= 0.75:
            return 1.15
        elif pcr < 1:
            return 1.1
        elif pcr < 2:
            return 1
        elif pcr < 3:
            return 0.9
        elif pcr < 5:
            return 0.8
        elif pcr < 10:
            return 0.7
        else:
            return 5

    elif product in ('Purchase_7', 'Purchase_10'):
        if pcr <= 0.75:
            return 1.75
        elif pcr < 1:
            return 1.5
        elif pcr <= 1.24:
            return 1.35
        elif pcr < 1.5:
            return 1.2
        elif pcr <= 2:
            return 1.1
        elif pcr < 3:
            return 1
        elif pcr < 7:
            return 0.85
        elif pcr < 10:
            return 0.7
        else:
            return 0.6

def final_failure_rate(r1, r2, r3, r4, r5, r6, r7, r8=1, r9=1):
    return (r1 * r2 * r3 * r4 * r5 * r6 * r7 * r8 * r9)

def monthly_loss_rate_func(product, failure_rate, brand_unit_failure_rate):
    if product in ('New_7', 'New_10'):
        r1 = round(failure_rate / 54, 10)
        r2 = round((brand_unit_failure_rate + failure_rate) / 108, 10)
        r3 = round(brand_unit_failure_rate / 54, 10)
        monthly_loss_rate = [0]
        for month in range(1, 85):
            if month <= 6:
                monthly_loss_rate.append(0)
            elif month <= 48:
                monthly_loss_rate.append(r1)
            elif month <= 72:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r1)
                else:
                    monthly_loss_rate.append(r2)
            else:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r1)
                else:
                    monthly_loss_rate.append(r3)

        return monthly_loss_rate

    elif product in ('Recap_7'):
        r1 = round(failure_rate / 49.2, 10)
        r2 = round(2 * failure_rate / 49.2, 10)
        r3 = round(3 * failure_rate / 49.2, 10)
        r4 = round(4 * failure_rate / 49.2, 10)
        r5 = round(9 * failure_rate / 98.4, 10)
        r6 = round(9 * (failure_rate + brand_unit_failure_rate) / 196.8, 10)
        r7 = round(failure_rate / 12.3, 10)
        r8 = round((failure_rate + brand_unit_failure_rate) / 24.6, 10)
        r9 = round(brand_unit_failure_rate / 12.3, 10)

        monthly_loss_rate = [0]
        for month in range(1, 85):
            if month <= 6:
                monthly_loss_rate.append(0)
            elif month <= 12:
                monthly_loss_rate.append(r1)
            elif month <= 18:
                monthly_loss_rate.append(r2)
            elif month <= 24:
                monthly_loss_rate.append(r3)
            elif month <= 48:
                monthly_loss_rate.append(r4)
            elif month <= 54:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r5)
                else:
                    monthly_loss_rate.append(r6)
            elif month <= 72:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r7)
                else:
                    monthly_loss_rate.append(r8)
            else:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r7)
                else:
                    monthly_loss_rate.append(r9)

        return monthly_loss_rate

    elif product in ('Recap_10', 'Purchase_7', 'Purchase_10'):
        r1 = round(failure_rate / 48, 10)
        r2 = round(2 * failure_rate / 48, 10)
        r3 = round(3 * failure_rate / 48, 10)
        r4 = round(4 * failure_rate / 48, 10)
        r5 = round(failure_rate / 12, 10)
        r6 = round((failure_rate + brand_unit_failure_rate) / 24, 10)
        r7 = round(brand_unit_failure_rate / 12, 10)

        monthly_loss_rate = [0]
        for month in range(1, 85):
            if month <= 6:
                monthly_loss_rate.append(0)
            elif month <= 12:
                monthly_loss_rate.append(r1)
            elif month <= 18:
                monthly_loss_rate.append(r2)
            elif month <= 24:
                monthly_loss_rate.append(r3)
            elif month <= 48:
                monthly_loss_rate.append(r4)
            elif month <= 72:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r5)
                else:
                    monthly_loss_rate.append(r6)
            else:
                if brand_unit_failure_rate < failure_rate:
                    monthly_loss_rate.append(r5)
                else:
                    monthly_loss_rate.append(r7)

        return monthly_loss_rate

def monthly_recovery_func(product, guarantee, monthly_balance_array, monthly_loss_rate_array,
                          monthly_asset_deprec_array, legal_fees):
    if product in ('New_7', 'Recap_7', 'Purchase_7', 'Purchase_10'):
        monthly_recovery_array = [0]

        for month in range(1, 85):
            if month <= 9:
                monthly_recovery_array.append(0)
            else:
                calc1 = monthly_loss_rate_array[month - 3] * (
                            guarantee + monthly_asset_deprec_array[month - 3] - legal_fees)
                calc2 = monthly_loss_rate_array[month - 3] * monthly_balance_array[month - 3]
                if guarantee < monthly_balance_array[month - 3]:
                    monthly_recovery_array.append(round(calc1, 6))
                else:
                    monthly_recovery_array.append(round(calc2, 6))

        return monthly_recovery_array

    elif product in ('New_10', 'Recap_10'):
        monthly_recovery_array = [0]

        for month in range(1, 85):
            if month <= 2:
                monthly_recovery_array.append(0)
            else:
                calc1 = monthly_loss_rate_array[month - 3] * (
                            guarantee + monthly_asset_deprec_array[month - 3] - legal_fees)
                calc2 = monthly_loss_rate_array[month - 3] * monthly_balance_array[month - 3]
                if guarantee < monthly_balance_array[month - 3]:
                    monthly_recovery_array.append(round(calc1, 6))
                else:
                    monthly_recovery_array.append(round(calc2, 6))

        return monthly_recovery_array

def monthly_open_accounts_func(product, monthly_loss_rate_array):
    if product in ('New_7', 'Recap_7', 'Purchase_7'):
        monthly_open_accounts_array = [1]

        for month in range(1, 85):
            if month <= 13:
                monthly_open_accounts_array.append(
                    round(monthly_open_accounts_array[month - 1] - monthly_loss_rate_array[month - 1], 8))
            elif month <= 73:
                monthly_open_accounts_array.append(
                    round(monthly_open_accounts_array[month - 1] - monthly_loss_rate_array[month - 1] - 0.25 / 100, 8))
            elif month <= 79:
                monthly_open_accounts_array.append(
                    round(monthly_open_accounts_array[month - 1] - monthly_loss_rate_array[month - 1] - 0.5 / 100, 8))
            else:
                monthly_open_accounts_array.append(
                    max(round(monthly_open_accounts_array[month - 1] - (monthly_open_accounts_array[79] / 6), 8), 0))
        return monthly_open_accounts_array

    elif product in ('New_10', 'Recap_10', 'Purchase_10'):
        monthly_open_accounts_array = [1]

        for month in range(1, 85):
            if month <= 13:
                monthly_open_accounts_array.append(
                    round(monthly_open_accounts_array[month - 1] - monthly_loss_rate_array[month - 1], 8))
            else:
                monthly_open_accounts_array.append(
                    round(monthly_open_accounts_array[month - 1] - monthly_loss_rate_array[month - 1] - 0.25 / 100, 8))
        return monthly_open_accounts_array

# ## End: Function creation for Pricing Model

# ## Product Specific Functions

def new():
    global fields
    monthlyPayment = monthly_payment(product, loanAmount, interestRate, terms, gracePeriod)
    monthlyBalanceArray = monthly_balance_func(product, loanAmount, interestRate, terms, gracePeriod)

    downPaymentMultiplier = down_payment_multiplier(product, borrowerExperience, downPaymentPercent)

    unitFailureMultiplier = brand_unit_failure_multiplier(product, brandCategory)

    gdscrMultiplier = gdscr_multiplier(gdscr)

    operatorExperienceMultiplier = borrower_exp_multiplier(operatorExperience)

    personalCreditMultiplier = personal_credit_multiplier(fico)

    pcrMultiplier = pcr_multiplier(product, pcr)

    riskFlagMultiplier = risk_flag_multiplier(nbrOfAows)

    finalFailureRate = final_failure_rate(downPaymentMultiplier, unitFailureMultiplier, gdscrMultiplier,
                                          operatorExperienceMultiplier, personalCreditMultiplier, pcrMultiplier,
                                          riskFlagMultiplier)

    monthlyLossRateArray = monthly_loss_rate_func(product, finalFailureRate, unitFailureMultiplier)

    monthlyGrossLossArray = monthly_gross_loss_func(monthlyBalanceArray, monthlyLossRateArray)

    monthlyAssetDeprecArray = monthly_asset_deprec_func(equipmentGuarantee)

    monthlyRecoveryArray = monthly_recovery_func(product, guarantee, monthlyBalanceArray, monthlyLossRateArray,
                                                 monthlyAssetDeprecArray, legalFees)

    monthlyNetLossArray = monthly_net_loss_func(monthlyGrossLossArray, monthlyRecoveryArray)

    totalNetLoss = total_loss(monthlyNetLossArray)

    monthlyOpenAcctArray = monthly_open_accounts_func(product, monthlyLossRateArray)

    portfolioBalanceArray = monthly_portfolio_balance_func(monthlyOpenAcctArray, monthlyBalanceArray)

    avgPortfolioBalance = avg_portfolio_balance(portfolioBalanceArray)

    cumulativeNetLossRate = cuml_net_loss_rate(totalNetLoss, avgPortfolioBalance)

    annualNetLossRate = annl_net_loss_rate(cumulativeNetLossRate)

    investmentGrade = investment_grade(annualNetLossRate)

    fields = {'investmentGrade': investmentGrade,
              'product': product,
              'loanAmount': loanAmount,
              'interestRate': interestRate,
              'terms': terms,
              'gracePeriod': gracePeriod,
              'monthlyPayment': monthlyPayment,
              'borrowerExperience': borrowerExperience,
              'downPaymentPercent': downPaymentPercent,
              'downPaymentMultiplier': downPaymentMultiplier,
              'brandCategory': brandCategory,
              'unitFailureMultiplier': unitFailureMultiplier,
              'gdscr': gdscr,
              'gdscrMultiplier': gdscrMultiplier,
              'operatorExperience': operatorExperience,
              'operatorExperienceMultiplier': operatorExperienceMultiplier,
              'fico': fico,
              'personalCreditMultiplier': personalCreditMultiplier,
              'pcr': pcr,
              'pcrMultiplier': pcrMultiplier,
              'nbrOfAows': nbrOfAows,
              'riskFlagMultiplier': riskFlagMultiplier,
              'finalFailureRate': finalFailureRate,
              'equipmentGuarantee': equipmentGuarantee,
              'guarantee': guarantee,
              'legalFees': legalFees,
              'totalNetLoss': totalNetLoss,
              'avgPortfolioBalance': avgPortfolioBalance,
              'cumulativeNetLossRate': cumulativeNetLossRate,
              'annualNetLossRate': annualNetLossRate
              }

    return fields

def recap():
    global fields
    monthlyPayment = monthly_payment(product, loanAmount, interestRate, terms, gracePeriod)
    monthlyBalanceArray = monthly_balance_func(product, loanAmount, interestRate, terms, gracePeriod)

    loanPurposeMultiplier = loan_purpose_multiplier(useOfFunds)

    timeInBusinessMultiplier = time_in_biz_multiplier(monthsSinceBreakeven)

    unitFailureMultiplier = brand_unit_failure_multiplier(product, brandCategory)

    franchsiorExperienceMultiplier = franchisor_exp_multiplier(franchisorExperience)

    fccrMultiplier = fccr_multiplier(fccr, fccrBasis)

    personalCreditMultiplier = personal_credit_multiplier(fico)

    intelliscoreMultiplier = intelliscore_multiplier(intelliscore)

    pcrMultiplier = pcr_multiplier(product, pcr)

    riskFlagMultiplier = risk_flag_multiplier(nbrOfAows)

    finalFailureRate = final_failure_rate(loanPurposeMultiplier, timeInBusinessMultiplier, unitFailureMultiplier,
                                          franchsiorExperienceMultiplier, fccrMultiplier, personalCreditMultiplier,
                                          intelliscoreMultiplier, pcrMultiplier, riskFlagMultiplier)

    monthlyLossRateArray = monthly_loss_rate_func(product, finalFailureRate, unitFailureMultiplier)

    monthlyGrossLossArray = monthly_gross_loss_func(monthlyBalanceArray, monthlyLossRateArray)

    monthlyAssetDeprecArray = monthly_asset_deprec_func(equipmentGuarantee)

    monthlyRecoveryArray = monthly_recovery_func(product, guarantee, monthlyBalanceArray, monthlyLossRateArray,
                                                 monthlyAssetDeprecArray, legalFees)

    monthlyNetLossArray = monthly_net_loss_func(monthlyGrossLossArray, monthlyRecoveryArray)

    totalNetLoss = total_loss(monthlyNetLossArray)

    monthlyOpenAcctArray = monthly_open_accounts_func(product, monthlyLossRateArray)

    portfolioBalanceArray = monthly_portfolio_balance_func(monthlyOpenAcctArray, monthlyBalanceArray)

    avgPortfolioBalance = avg_portfolio_balance(portfolioBalanceArray)

    cumulativeNetLossRate = cuml_net_loss_rate(totalNetLoss, avgPortfolioBalance)

    annualNetLossRate = annl_net_loss_rate(cumulativeNetLossRate)

    investmentGrade = investment_grade(annualNetLossRate)

    fields = {'investmentGrade': investmentGrade,
              'product': product,
              'loanAmount': loanAmount,
              'interestRate': interestRate,
              'terms': terms,
              'gracePeriod': gracePeriod,
              'monthlyPayment': monthlyPayment,
              'useOfFunds': useOfFunds,
              'loanPurposeMultiplier': loanPurposeMultiplier,
              'monthsSinceBreakeven': monthsSinceBreakeven,
              'timeInBusinessMultiplier': timeInBusinessMultiplier,
              'brandCategory': brandCategory,
              'unitFailureMultiplier': unitFailureMultiplier,
              'franchisorExperience': franchisorExperience,
              'franchsiorExperienceMultiplier': franchsiorExperienceMultiplier,
              'fccr': fccr,
              'fccrBasis': fccrBasis,
              'fccrMultiplier': fccrMultiplier,
              'fico': fico,
              'personalCreditMultiplier': personalCreditMultiplier,
              'intelliscore': intelliscore,
              'intelliscoreMultiplier': intelliscoreMultiplier,
              'pcr': pcr,
              'pcrMultiplier': pcrMultiplier,
              'nbrOfAows': nbrOfAows,
              'riskFlagMultiplier': riskFlagMultiplier,
              'finalFailureRate': finalFailureRate,
              'equipmentGuarantee': equipmentGuarantee,
              'guarantee': guarantee,
              'legalFees': legalFees,
              'totalNetLoss': totalNetLoss,
              'avgPortfolioBalance': avgPortfolioBalance,
              'cumulativeNetLossRate': cumulativeNetLossRate,
              'annualNetLossRate': annualNetLossRate
              }

    return fields

def purchase():
    global fields
    monthlyPayment = monthly_payment(product, loanAmount, interestRate, terms, gracePeriod)
    monthlyBalanceArray = monthly_balance_func(product, loanAmount, interestRate, terms, gracePeriod)

    downPaymentMultiplier = down_payment_multiplier(product, borrowerExperience, downPaymentPercent)

    unitFailureMultiplier = brand_unit_failure_multiplier(product, brandCategory)

    timeInBusinessMultiplier = time_in_biz_multiplier(monthsSinceBreakeven)

    fccrMultiplier = fccr_multiplier(fccr, fccrBasis)

    operatorExperienceMultiplier = borrower_exp_multiplier(operatorExperience)

    personalCreditMultiplier = personal_credit_multiplier(fico)

    pcrMultiplier = pcr_multiplier(product, pcr)

    riskFlagMultiplier = risk_flag_multiplier(nbrOfAows)

    finalFailureRate = final_failure_rate(riskFlagMultiplier, pcrMultiplier, personalCreditMultiplier,
                                          operatorExperienceMultiplier, fccrMultiplier, timeInBusinessMultiplier,
                                          downPaymentMultiplier, unitFailureMultiplier)

    monthlyLossRateArray = monthly_loss_rate_func(product, finalFailureRate, unitFailureMultiplier)

    monthlyGrossLossArray = monthly_gross_loss_func(monthlyBalanceArray, monthlyLossRateArray)

    monthlyAssetDeprecArray = monthly_asset_deprec_func(equipmentGuarantee)

    monthlyRecoveryArray = monthly_recovery_func(product, guarantee, monthlyBalanceArray, monthlyLossRateArray,
                                                 monthlyAssetDeprecArray, legalFees)

    monthlyNetLossArray = monthly_net_loss_func(monthlyGrossLossArray, monthlyRecoveryArray)

    totalNetLoss = total_loss(monthlyNetLossArray)

    monthlyOpenAcctArray = monthly_open_accounts_func(product, monthlyLossRateArray)

    portfolioBalanceArray = monthly_portfolio_balance_func(monthlyOpenAcctArray, monthlyBalanceArray)

    avgPortfolioBalance = avg_portfolio_balance(portfolioBalanceArray)

    cumulativeNetLossRate = cuml_net_loss_rate(totalNetLoss, avgPortfolioBalance)

    annualNetLossRate = annl_net_loss_rate(cumulativeNetLossRate)

    investmentGrade = investment_grade(annualNetLossRate)

    fields = {'investmentGrade': investmentGrade,
              'product': product,
              'loanAmount': loanAmount,
              'interestRate': interestRate,
              'terms': terms,
              'gracePeriod': gracePeriod,
              'monthlyPayment': monthlyPayment,
              'borrowerExperience': borrowerExperience,
              'downPaymentPercent': downPaymentPercent,
              'downPaymentMultiplier': downPaymentMultiplier,
              'brandCategory': brandCategory,
              'unitFailureMultiplier': unitFailureMultiplier,
              'monthsSinceBreakeven': monthsSinceBreakeven,
              'timeInBusinessMultiplier': timeInBusinessMultiplier,
              'fccr': fccr,
              'fccrBasis': fccrBasis,
              'fccrMultiplier': fccrMultiplier,
              'operatorExperience': operatorExperience,
              'operatorExperienceMultiplier': operatorExperienceMultiplier,
              'fico': fico,
              'personalCreditMultiplier': personalCreditMultiplier,
              'pcr': pcr,
              'pcrMultiplier': pcrMultiplier,
              'nbrOfAows': nbrOfAows,
              'riskFlagMultiplier': riskFlagMultiplier,
              'finalFailureRate': finalFailureRate,
              'equipmentGuarantee': equipmentGuarantee,
              'guarantee': guarantee,
              'legalFees': legalFees,
              'totalNetLoss': totalNetLoss,
              'avgPortfolioBalance': avgPortfolioBalance,
              'cumulativeNetLossRate': cumulativeNetLossRate,
              'annualNetLossRate': annualNetLossRate
              }

    return fields





