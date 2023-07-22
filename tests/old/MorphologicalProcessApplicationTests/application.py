

from old_src.langcode import Morpheme
from tests.old.abstractTest import AbstractTest


class ApplicationTest(AbstractTest):
	@classmethod
	def _get_test_name(cls) -> str:
		return 'Application'

	is_generated = False

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if not self.is_generated:
			self.gen_all_test_morpheme_processes()
			self.is_generated = True

	morpheme_change_parameters = [
		('prefix',             					Morpheme, {'over+':    				  [('cook', 'overcook'), ('look', 'overlook')]}),
		('postfix',   	   	   					Morpheme, {'+ful':     				  [('wonder', 'wonderful'), ('stress', 'stressful')]}),
		('optional_postfix',   					Morpheme, {'-e^n+t':            	  [('üben', 'übt'), ('sammeln', 'sammelt')]}),
		('cond_postfix',   	        			Morpheme, {'(-a|-o?-),(-a?+y:+a)':    [('kot', 'kota'), ('mama', 'mamy'), ('okno', 'okna')]}),
		('autogrouping_infix',      			Morpheme, {r'-ek+usz\1':  	          [('kwiatek', 'kwiatuszek')],
								 	           			   r'u-\1r+':    		      [('umat', 'urmat'), ('ukat', 'urkat')]}),
		('context_grouping_jointly_infix', 	    Morpheme, {r'V1C*1-~V1-V1+r+': 		  [('umat', 'urmat'), ('amat', 'armat')]}),
		('context_grouping_separately_infix', 	Morpheme, {r'V1C*1-~V1-,r+,V1+': 	  [('umat', 'urmat'), ('amat', 'armat')]}),
		('circumfix',      	 					Morpheme, {'ge+t':     				  [('sag', 'gesagt'), ]}),
		('interfix',         					Morpheme, {'+o+':      				  [('myśl', 'zbrodnia', 'myślozbrodnia'),
											  	  				   	  				   ('kot', 'schron', 'kotoschron'),
											      				       				   ('kot', 'pies', 'kotopies'),
																	   				   ('marsz', 'bieg', 'marszobieg')]}),
		('umlaut_simulfix', 		 			Morpheme, {'-V1C1~V1:u>ü|o>ö|a>ä':    [('groß', 'größer')]}),
		#('syllable_simulfix', 		 			Morpheme, {'-V1C1~V1:u>ü|o>ö|a>ä':    [('groß', 'größer')]}),
		('mutation_simulfix', 		 			Morpheme, {'-C1:k>cz,+ek': [('paweł', 'pawełek'), ('pawełek', 'pawełeczek')],
														   '-C1~C1:k>cz,+ek':    [('paweł', 'pawełek'), ('pawełek', 'pawełeczek')]}),
	]

	@classmethod
	def gen_all_test_morpheme_processes(cls):
		param_num = 3
		adjust_params = lambda params: (list(params) + [None]*param_num)[:param_num]
		for (op_name, morpheme_class, forms_pairs) in map(adjust_params, cls.morpheme_change_parameters):
			for form, to_apply_tos_expecteds in forms_pairs.items():
				for to_apply_tos_expected in to_apply_tos_expecteds:
					to_apply_tos = to_apply_tos_expected[:-1]
					expected = to_apply_tos_expecteds[-1]
					to_apply_to_str = '_and_'.join(to_apply_tos)
					test_name = f'test_apply_{op_name}_on_{to_apply_to_str}_to_get_{expected}_using_{morpheme_class.__name__.lower()}'
					print(test_name)
					test = cls.gen_test_morpheme_process(morpheme_class, form, to_apply_tos, expected)
					setattr(ApplicationTest, test_name, test)

	@classmethod
	def gen_test_morpheme_process(cls, morpheme_class: type[Morpheme], form: str, to_apply_tos: list[str], expected: str):
		def test_morpheme_process(self, *args):
			morpheme = morpheme_class(form)
			actual = morpheme(*to_apply_tos)
			self.assertEqual(expected, actual)
		return test_morpheme_process

	# #  name_func=lambda method, param_num, param: f'{method.__name__}_{param_num}_apply_{param.args[0]}_with_{param.args[2].__name__}')
	# @parameterized.expand([
	# 	('add_prefix_with_morpheme', Morpheme, 'over+', ['cook'], ['overcook']),
	# 	('', '', Morpheme),
	# 	('', '', Morpheme),
	# 	('', '', Morpheme),
	# ])
	# def apply_form_test(self, name, morpheme, form, to_applies, expecteds):
	# 	pass